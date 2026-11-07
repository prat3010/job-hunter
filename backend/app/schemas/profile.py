from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class UserProfileBase(BaseModel):
    full_name: str = "Software Engineer"
    headline: Optional[str] = None
    bio: Optional[str] = None
    target_roles: List[str] = []
    skills: List[str] = []
    negative_keywords: List[str] = []
    preferred_locations: List[str] = []
    min_salary: int = 0
    resume_raw_text: Optional[str] = None

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    target_roles: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    negative_keywords: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    min_salary: Optional[int] = None
    resume_raw_text: Optional[str] = None

class UserProfileResponse(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime

class ResumeParseResponse(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    suggested_target_roles: List[str] = []
    suggested_skills: List[str] = []
    suggested_negative_keywords: List[str] = []
    raw_text: str

class AIConfigBase(BaseModel):
    provider: str = "gemini" # 'gemini', 'openai', 'anthropic', 'groq', 'ollama'
    model_name: str = "gemini-2.5-flash"
    ollama_url: str = "http://localhost:11434"
    auto_scan_interval_hours: int = 0
    enabled_boards: List[str] = []

class AIConfigUpdate(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    ollama_url: Optional[str] = None
    auto_scan_interval_hours: Optional[int] = None
    enabled_boards: Optional[List[str]] = None

class AIConfigResponse(AIConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    has_api_key: bool
    masked_api_key: str
    updated_at: datetime
