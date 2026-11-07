import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class JobLead(Base):
    __tablename__ = "job_leads"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    company = Column(String(255), nullable=False, index=True)
    role = Column(String(255), nullable=False, index=True)
    source_url = Column(String(1024), nullable=False, unique=True, index=True)
    intent_source = Column(String(100), nullable=False, index=True)
    lead_type = Column(String(50), nullable=False, default="job", index=True) # 'job' or 'client'
    
    snippet = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)
    compensation = Column(String(255), nullable=True)
    compensation_inr = Column(String(255), nullable=True)
    
    quality_score = Column(Integer, default=0, index=True)
    propensity_tier = Column(String(50), default="B Qualified", index=True) # 'A+ High Value', 'B Qualified', 'C Low Priority'
    verification_reason = Column(Text, nullable=True)
    
    # Kanban Status: 'discovered', 'shortlisted', 'pitch_generated', 'applied', 'interviewing', 'archived'
    status = Column(String(50), default="discovered", index=True)
    notes = Column(Text, nullable=True)
    
    # Generated Pitches
    pitch_email = Column(Text, nullable=True)
    pitch_linkedin = Column(Text, nullable=True)
    pitch_elevator = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
