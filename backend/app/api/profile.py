import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.profile import UserProfile, AIConfig
from app.schemas.profile import (
    UserProfileResponse, UserProfileUpdate, ResumeParseResponse
)
from app.services.matcher import GLOBAL_MATCHER
from app.services.resume_parser import ResumeParser

router = APIRouter(prefix="/profile", tags=["Profile"])

def _format_profile_response(profile: UserProfile) -> UserProfileResponse:
    return UserProfileResponse(
        id=profile.id,
        full_name=profile.full_name,
        headline=profile.headline,
        bio=profile.bio,
        target_roles=json.loads(profile.target_roles or "[]"),
        skills=json.loads(profile.skills or "[]"),
        negative_keywords=json.loads(profile.negative_keywords or "[]"),
        preferred_locations=json.loads(profile.preferred_locations or "[]"),
        min_salary=profile.min_salary,
        resume_raw_text=profile.resume_raw_text,
        updated_at=profile.updated_at
    )

@router.get("", response_model=UserProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not initialized")
    return _format_profile_response(profile)

@router.put("", response_model=UserProfileResponse)
def update_profile(payload: UserProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        profile = UserProfile(id=1)
        db.add(profile)

    if payload.full_name is not None:
        profile.full_name = payload.full_name
    if payload.headline is not None:
        profile.headline = payload.headline
    if payload.bio is not None:
        profile.bio = payload.bio
    if payload.target_roles is not None:
        profile.target_roles = json.dumps(payload.target_roles)
    if payload.skills is not None:
        profile.skills = json.dumps(payload.skills)
    if payload.negative_keywords is not None:
        profile.negative_keywords = json.dumps(payload.negative_keywords)
    if payload.preferred_locations is not None:
        profile.preferred_locations = json.dumps(payload.preferred_locations)
    if payload.min_salary is not None:
        profile.min_salary = payload.min_salary
    if payload.resume_raw_text is not None:
        profile.resume_raw_text = payload.resume_raw_text

    db.commit()
    db.refresh(profile)

    # Re-index global semantic matcher
    GLOBAL_MATCHER.fit_profile(profile.to_dict())

    return _format_profile_response(profile)

@router.post("/upload-resume", response_model=ResumeParseResponse)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload resume PDF or text document and extract structured candidate profile."""
    content = await file.read()
    if not content or len(content.strip()) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    filename = (file.filename or "").lower()

    if filename.endswith(".pdf"):
        try:
            extracted_text = ResumeParser.extract_text_from_pdf(content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        try:
            extracted_text = content.decode("utf-8")
        except Exception:
            extracted_text = content.decode("latin-1", errors="ignore")
        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Uploaded text document contains no readable text content."
            )

    ai_cfg = db.query(AIConfig).first()
    ai_dict = {
        "provider": ai_cfg.provider if ai_cfg else "gemini",
        "api_key": ai_cfg.api_key if ai_cfg else "",
        "model_name": ai_cfg.model_name if ai_cfg else "gemini-2.5-flash",
        "ollama_url": ai_cfg.ollama_url if ai_cfg else "http://localhost:11434"
    }

    parsed = ResumeParser.parse_profile_from_text(extracted_text, ai_dict)
    return ResumeParseResponse(**parsed)
