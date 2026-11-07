import json
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("job_hunter.scheduler")
scheduler = BackgroundScheduler()

def scheduled_scan_job():
    """Execute scheduled background scan across enabled boards."""
    from app.core.database import SessionLocal
    from app.models.profile import UserProfile, AIConfig
    from app.models.job import JobLead
    from app.services.scrapers import run_scanners
    
    logger.info("Executing scheduled background scan...")
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        ai_cfg = db.query(AIConfig).first()
        if not profile or not ai_cfg:
            return

        enabled_boards = json.loads(ai_cfg.enabled_boards or "[]")
        known_urls = {j.source_url for j in db.query(JobLead.source_url).all()}
        discovered = run_scanners(
            board_ids=enabled_boards,
            known_urls=known_urls,
            profile_data=profile.to_dict(),
            min_score=65
        )

        new_count = 0
        for item in discovered:
            lead = JobLead(**item)
            db.add(lead)
            new_count += 1
        db.commit()
        logger.info(f"Scheduled scan completed: {new_count} new leads added.")
    except Exception as e:
        logger.error(f"Scheduled scan error: {e}")
        db.rollback()
    finally:
        db.close()

def start_scheduler():
    try:
        if not scheduler.running:
            scheduler.start()
            logger.info("Background scheduler started.")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

def stop_scheduler():
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Background scheduler stopped.")
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")

def update_schedule(interval_hours: int):
    try:
        job_id = "periodic_scan"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        if interval_hours > 0:
            scheduler.add_job(
                scheduled_scan_job,
                trigger=IntervalTrigger(hours=interval_hours),
                id=job_id,
                name="Periodic Job Scanner",
                replace_existing=True
            )
            logger.info(f"Scheduled periodic scan every {interval_hours} hours.")
        else:
            logger.info("Periodic scan disabled.")
    except Exception as e:
        logger.error(f"Failed to update schedule: {e}")
