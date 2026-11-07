import json
import asyncio
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.models.job import JobLead
from app.models.profile import UserProfile, AIConfig
from app.schemas.job import ScanTriggerRequest, ScanStatusResponse
from app.services.scrapers import (
    AVAILABLE_BOARDS, BOARD_SCRAPER_MAP, run_scanners
)

router = APIRouter(prefix="/scan", tags=["Scanner"])

@router.get("/boards")
def list_boards(db: Session = Depends(get_db)):
    """List all available scraping boards and their enabled status."""
    ai_cfg = db.query(AIConfig).first()
    enabled = json.loads(ai_cfg.enabled_boards or "[]") if ai_cfg else []
    
    return [
        {
            "id": b["id"],
            "name": b["name"],
            "enabled": b["id"] in enabled if enabled else True
        }
        for b in AVAILABLE_BOARDS
    ]

@router.post("", response_model=ScanStatusResponse)
def trigger_scan(payload: ScanTriggerRequest, db: Session = Depends(get_db)):
    """Trigger a live scan across requested or enabled boards."""
    profile = db.query(UserProfile).first()
    ai_cfg = db.query(AIConfig).first()
    
    board_ids = payload.board_ids
    if not board_ids and ai_cfg:
        board_ids = json.loads(ai_cfg.enabled_boards or "[]")

    known_urls = {j.source_url for j in db.query(JobLead.source_url).all()}
    
    profile_dict = profile.to_dict() if profile else {}

    board_progress = []
    
    def on_progress(bid, name, status, found, err):
        existing = next((b for b in board_progress if b["board_id"] == bid), None)
        if existing:
            existing["status"] = status
            existing["found_count"] = found
            existing["error"] = err
        else:
            board_progress.append({
                "board_id": bid,
                "name": name,
                "status": status,
                "found_count": found,
                "error": err
            })

    discovered = run_scanners(
        board_ids=board_ids,
        known_urls=known_urls,
        profile_data=profile_dict,
        min_score=payload.min_quality_score,
        progress_callback=on_progress
    )

    new_saved = 0
    for item in discovered:
        # Check if already inserted during this run
        if not db.query(JobLead).filter(JobLead.source_url == item["source_url"]).first():
            lead = JobLead(**item)
            db.add(lead)
            new_saved += 1
            
    db.commit()

    return {
        "is_scanning": False,
        "total_found": new_saved,
        "boards": board_progress
    }

@router.get("/stream")
async def stream_scan(
    board_ids: Optional[str] = Query(None, description="Comma-separated board IDs"),
    min_score: int = Query(65, ge=0, le=100)
):
    """Server-Sent Events (SSE) live scan stream for real-time UI feedback."""
    parsed_boards = [b.strip() for b in board_ids.split(",")] if board_ids else None

    async def event_generator():
        db = SessionLocal()
        try:
            profile = db.query(UserProfile).first()
            ai_cfg = db.query(AIConfig).first()
            
            b_ids = parsed_boards
            if not b_ids and ai_cfg:
                b_ids = json.loads(ai_cfg.enabled_boards or "[]")
            if not b_ids:
                b_ids = list(BOARD_SCRAPER_MAP.keys())

            known_urls = {j.source_url for j in db.query(JobLead.source_url).all()}
            profile_dict = profile.to_dict() if profile else {}

            total_new_leads = 0

            for bid in b_ids:
                if bid not in BOARD_SCRAPER_MAP:
                    continue
                name, scraper_func = BOARD_SCRAPER_MAP[bid]
                
                # Yield scanning event
                yield f"data: {json.dumps({'type': 'board_start', 'board_id': bid, 'name': name})}\n\n"
                await asyncio.sleep(0.05)

                try:
                    # Run scraper synchronously in executor to avoid blocking async event loop
                    loop = asyncio.get_event_loop()
                    leads = await loop.run_in_executor(None, scraper_func, known_urls, profile_dict, min_score)
                    
                    saved_for_board = 0
                    for item in leads:
                        if item["source_url"] not in known_urls:
                            lead = JobLead(**item)
                            db.add(lead)
                            known_urls.add(item["source_url"])
                            saved_for_board += 1
                            total_new_leads += 1
                    
                    db.commit()

                    yield f"data: {json.dumps({'type': 'board_complete', 'board_id': bid, 'name': name, 'found': saved_for_board})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'board_error', 'board_id': bid, 'name': name, 'error': str(e)})}\n\n"

            yield f"data: {json.dumps({'type': 'scan_finished', 'total_new_leads': total_new_leads})}\n\n"
        finally:
            db.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
