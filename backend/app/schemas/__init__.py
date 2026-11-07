from app.schemas.job import (
    JobLeadCreate, JobLeadUpdate, JobLeadResponse, 
    JobLeadListResponse, PitchGenerateRequest, PitchGenerateResponse,
    ScanTriggerRequest, ScanStatusResponse
)
from app.schemas.profile import (
    UserProfileUpdate, UserProfileResponse,
    AIConfigUpdate, AIConfigResponse
)

__all__ = [
    "JobLeadCreate", "JobLeadUpdate", "JobLeadResponse", "JobLeadListResponse",
    "PitchGenerateRequest", "PitchGenerateResponse", "ScanTriggerRequest", "ScanStatusResponse",
    "UserProfileUpdate", "UserProfileResponse", "AIConfigUpdate", "AIConfigResponse"
]
