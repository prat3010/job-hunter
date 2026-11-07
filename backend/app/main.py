import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.models.profile import UserProfile, AIConfig
from app.services.matcher import GLOBAL_MATCHER
from app.services.scheduler import start_scheduler, stop_scheduler, update_schedule

from app.api.jobs import router as jobs_router
from app.api.scan import router as scan_router
from app.api.profile import router as profile_router
from app.api.pitches import router as pitches_router
from app.api.settings import router as settings_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database & Seed
    init_db()
    
    # Initialize Global Matcher with active User Profile
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        if profile:
            GLOBAL_MATCHER.fit_profile(profile.to_dict())

        ai_cfg = db.query(AIConfig).first()
        if ai_cfg and ai_cfg.auto_scan_interval_hours > 0:
            start_scheduler()
            update_schedule(ai_cfg.auto_scan_interval_hours)
    finally:
        db.close()

    yield

    # Shutdown
    stop_scheduler()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(jobs_router, prefix=settings.API_PREFIX)
app.include_router(scan_router, prefix=settings.API_PREFIX)
app.include_router(profile_router, prefix=settings.API_PREFIX)
app.include_router(pitches_router, prefix=settings.API_PREFIX)
app.include_router(settings_router, prefix=settings.API_PREFIX)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
