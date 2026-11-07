from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.core.database import get_db
from app.models.job import JobLead
from app.schemas.job import (
    JobLeadResponse, JobLeadListResponse, JobLeadUpdate, JobLeadCreate
)

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("", response_model=JobLeadListResponse)
def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status (discovered, shortlisted, pitch_generated, applied, interviewing, archived)"),
    lead_type: Optional[str] = Query(None, description="Filter by lead type (job or client)"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum quality score"),
    tier: Optional[str] = Query(None, description="Propensity tier (A+ High Value, B Qualified, C Low Priority)"),
    search: Optional[str] = Query(None, description="Search term in company, role, or snippet"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(JobLead)

    if status and status != "all":
        query = query.filter(JobLead.status == status)
    else:
        # By default exclude archived from main views unless explicitly requested
        if status != "archived":
            query = query.filter(JobLead.status != "archived")

    if lead_type and lead_type != "all":
        query = query.filter(JobLead.lead_type == lead_type)

    if min_score is not None:
        query = query.filter(JobLead.quality_score >= min_score)

    if tier and tier != "all":
        query = query.filter(JobLead.propensity_tier == tier)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                JobLead.company.ilike(s),
                JobLead.role.ilike(s),
                JobLead.snippet.ilike(s),
                JobLead.verification_reason.ilike(s)
            )
        )

    total = query.count()
    items = query.order_by(desc(JobLead.quality_score), desc(JobLead.created_at))\
                 .offset((page - 1) * page_size)\
                 .limit(page_size)\
                 .all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }

@router.get("/stats")
def get_job_stats(db: Session = Depends(get_db)):
    """Aggregate counts per status for Kanban badges and header metrics."""
    statuses = ["discovered", "shortlisted", "pitch_generated", "applied", "interviewing", "archived"]
    counts = {s: 0 for s in statuses}
    
    leads = db.query(JobLead.status).all()
    for (lead_status,) in leads:
        if lead_status in counts:
            counts[lead_status] += 1
            
    total_active = sum(counts[s] for s in ["discovered", "shortlisted", "pitch_generated", "applied", "interviewing"])
    return {
        "total_active": total_active,
        "counts": counts
    }

@router.get("/{job_id}", response_model=JobLeadResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    lead = db.query(JobLead).filter(JobLead.id == job_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Job lead not found")
    return lead

@router.post("", response_model=JobLeadResponse, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobLeadCreate, db: Session = Depends(get_db)):
    existing = db.query(JobLead).filter(JobLead.source_url == payload.source_url).first()
    if existing:
        raise HTTPException(status_code=409, detail="Job lead with this URL already exists")
    lead = JobLead(**payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

@router.patch("/{job_id}", response_model=JobLeadResponse)
def update_job(job_id: str, payload: JobLeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(JobLead).filter(JobLead.id == job_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Job lead not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(lead, field, val)
        
    db.commit()
    db.refresh(lead)
    return lead

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    lead = db.query(JobLead).filter(JobLead.id == job_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Job lead not found")
    db.delete(lead)
    db.commit()
    return None
