import json
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.profile import AIConfig
from app.schemas.profile import AIConfigResponse, AIConfigUpdate
from app.services.llm_gateway import LLMGateway
from app.services.scheduler import update_schedule

router = APIRouter(prefix="/settings", tags=["Settings"])

def _format_ai_response(cfg: AIConfig) -> AIConfigResponse:
    has_key = bool(cfg.api_key and cfg.api_key.strip())
    masked = ""
    if has_key:
        k = cfg.api_key.strip()
        if len(k) > 8:
            masked = f"{k[:4]}****{k[-4:]}"
        else:
            masked = "****"

    return AIConfigResponse(
        id=cfg.id,
        provider=cfg.provider or "gemini",
        model_name=cfg.model_name or "gemini-2.5-flash",
        ollama_url=cfg.ollama_url or "http://localhost:11434",
        auto_scan_interval_hours=cfg.auto_scan_interval_hours or 0,
        enabled_boards=json.loads(cfg.enabled_boards or "[]"),
        has_api_key=has_key,
        masked_api_key=masked,
        updated_at=cfg.updated_at
    )

@router.get("", response_model=AIConfigResponse)
def get_settings(db: Session = Depends(get_db)):
    cfg = db.query(AIConfig).first()
    if not cfg:
        cfg = AIConfig(id=1)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return _format_ai_response(cfg)

@router.put("", response_model=AIConfigResponse)
def update_settings(payload: AIConfigUpdate, db: Session = Depends(get_db)):
    cfg = db.query(AIConfig).first()
    if not cfg:
        cfg = AIConfig(id=1)
        db.add(cfg)

    if payload.provider is not None:
        cfg.provider = payload.provider
    if payload.api_key is not None:
        cfg.api_key = payload.api_key
    if payload.model_name is not None:
        cfg.model_name = payload.model_name
    if payload.ollama_url is not None:
        cfg.ollama_url = payload.ollama_url
    if payload.auto_scan_interval_hours is not None:
        cfg.auto_scan_interval_hours = payload.auto_scan_interval_hours
        update_schedule(payload.auto_scan_interval_hours)
    if payload.enabled_boards is not None:
        cfg.enabled_boards = json.dumps(payload.enabled_boards)

    db.commit()
    db.refresh(cfg)
    return _format_ai_response(cfg)

@router.post("/test-connection")
def test_ai_connection(db: Session = Depends(get_db)):
    """Test AI model inference connection and calculate round-trip latency."""
    cfg = db.query(AIConfig).first()
    if not cfg:
        raise HTTPException(status_code=400, detail="AI config not found")

    ai_dict = {
        "provider": cfg.provider,
        "api_key": cfg.api_key,
        "model_name": cfg.model_name,
        "ollama_url": cfg.ollama_url
    }

    start = time.time()
    test_prompt = "Reply with 'CONNECTED' if you can read this."
    result = LLMGateway.generate_text(test_prompt, ai_dict)
    elapsed_ms = int((time.time() - start) * 1000)

    if result:
        return {
            "success": True,
            "provider": cfg.provider,
            "model": cfg.model_name,
            "latency_ms": elapsed_ms,
            "response": result[:100]
        }
    else:
        return {
            "success": False,
            "provider": cfg.provider,
            "model": cfg.model_name,
            "latency_ms": elapsed_ms,
            "error": "Failed to receive response from provider. Check API key or Ollama connection."
        }
