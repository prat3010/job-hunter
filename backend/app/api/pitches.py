import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import JobLead
from app.models.profile import UserProfile, AIConfig
from app.schemas.job import PitchGenerateRequest, PitchGenerateResponse
from app.services.llm_gateway import LLMGateway

router = APIRouter(prefix="/jobs", tags=["Pitches"])

@router.post("/{job_id}/pitch", response_model=PitchGenerateResponse)
def generate_job_pitch(
    job_id: str,
    payload: PitchGenerateRequest = PitchGenerateRequest(),
    db: Session = Depends(get_db)
):
    """Generate multi-channel outreach pitch for a job lead using BYOK AI or offline fallback."""
    lead = db.query(JobLead).filter(JobLead.id == job_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Job lead not found")

    profile = db.query(UserProfile).first()
    ai_cfg = db.query(AIConfig).first()

    profile_dict = {
        "full_name": profile.full_name if profile else "Software Engineer",
        "headline": profile.headline if profile else "Full-Stack Engineer",
        "bio": profile.bio if profile else "",
        "skills": json.loads(profile.skills or "[]") if profile else ["Python", "TypeScript", "React"],
        "target_roles": json.loads(profile.target_roles or "[]") if profile else []
    }

    ai_dict = {
        "provider": ai_cfg.provider if ai_cfg else "gemini",
        "api_key": ai_cfg.api_key if ai_cfg else "",
        "model_name": ai_cfg.model_name if ai_cfg else "gemini-2.5-flash",
        "ollama_url": ai_cfg.ollama_url if ai_cfg else "http://localhost:11434"
    }

    pitches = LLMGateway.generate_pitches(
        company=lead.company,
        role=lead.role,
        snippet=lead.description or lead.snippet or "",
        profile_data=profile_dict,
        ai_config=ai_dict,
        lead_type=lead.lead_type,
        focus_angle=payload.focus_angle
    )

    # Persist generated pitches to JobLead
    lead.pitch_email = pitches["email"]
    lead.pitch_linkedin = pitches["linkedin"]
    lead.pitch_elevator = pitches["elevator_pitch"]

    # Transition status to 'pitch_generated' if currently in discovery/shortlisted
    if lead.status in ["discovered", "shortlisted"]:
        lead.status = "pitch_generated"

    db.commit()
    db.refresh(lead)

    return PitchGenerateResponse(
        email=pitches["email"],
        linkedin=pitches["linkedin"],
        elevator_pitch=pitches["elevator_pitch"]
    )
