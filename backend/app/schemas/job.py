from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class JobLeadBase(BaseModel):
    company: str
    role: str
    source_url: str
    intent_source: str
    lead_type: str = "job"
    snippet: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    compensation: Optional[str] = None
    compensation_inr: Optional[str] = None
    quality_score: int = 0
    propensity_tier: str = "B Qualified"
    verification_reason: Optional[str] = None
    status: str = "discovered"
    notes: Optional[str] = None
    pitch_email: Optional[str] = None
    pitch_linkedin: Optional[str] = None
    pitch_elevator: Optional[str] = None

class JobLeadCreate(JobLeadBase):
    pass

class JobLeadUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    email: Optional[str] = None
    compensation: Optional[str] = None
    compensation_inr: Optional[str] = None
    quality_score: Optional[int] = None
    propensity_tier: Optional[str] = None
    pitch_email: Optional[str] = None
    pitch_linkedin: Optional[str] = None
    pitch_elevator: Optional[str] = None

class JobLeadResponse(JobLeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime

class JobLeadListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[JobLeadResponse]

class PitchGenerateRequest(BaseModel):
    focus_angle: Optional[str] = Field(
        default=None,
        description="Optional angle to emphasize: e.g. 'RAG', 'Agentic Workflows', 'Full-Stack Performance'"
    )

class PitchGenerateResponse(BaseModel):
    email: str
    linkedin: str
    elevator_pitch: str

class ScanTriggerRequest(BaseModel):
    board_ids: Optional[List[str]] = None
    min_quality_score: int = 65

class ScanBoardProgress(BaseModel):
    board_id: str
    name: str
    status: str # 'pending', 'scanning', 'completed', 'failed'
    found_count: int = 0
    error: Optional[str] = None

class ScanStatusResponse(BaseModel):
    is_scanning: bool
    total_found: int = 0
    boards: List[ScanBoardProgress] = []
