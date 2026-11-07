from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, default=1)
    full_name = Column(String(255), nullable=False, default="Software Engineer")
    headline = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Stored as JSON strings
    target_roles = Column(Text, nullable=False, default="[]")
    skills = Column(Text, nullable=False, default="[]")
    negative_keywords = Column(Text, nullable=False, default="[]")
    preferred_locations = Column(Text, nullable=False, default="[]")
    
    min_salary = Column(Integer, default=0)
    resume_raw_text = Column(Text, nullable=True)
    
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "full_name": self.full_name,
            "headline": self.headline or "",
            "bio": self.bio or "",
            "target_roles": json.loads(self.target_roles or "[]"),
            "skills": json.loads(self.skills or "[]"),
            "negative_keywords": json.loads(self.negative_keywords or "[]"),
            "preferred_locations": json.loads(self.preferred_locations or "[]"),
            "min_salary": self.min_salary or 0,
            "resume_raw_text": self.resume_raw_text or "",
            "updated_at": self.updated_at
        }

class AIConfig(Base):
    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, default=1)
    provider = Column(String(50), default="gemini") # 'gemini', 'openai', 'anthropic', 'groq', 'ollama'
    api_key = Column(String(512), default="")
    model_name = Column(String(100), default="gemini-2.5-flash")
    ollama_url = Column(String(255), default="http://localhost:11434")
    
    auto_scan_interval_hours = Column(Integer, default=0) # 0 = disabled
    enabled_boards = Column(Text, default="[]") # JSON list of enabled board ids
    
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
