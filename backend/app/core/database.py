from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Enable SQLite foreign key enforcement
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    import json
    from app.models.job import JobLead
    from app.models.profile import UserProfile, AIConfig
    
    Base.metadata.create_all(bind=engine)
    
    # Seed default UserProfile and AIConfig if table is empty
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        if not profile:
            default_profile = UserProfile(
                id=1,
                full_name="Software Engineer",
                headline="Full-Stack & AI Solutions Architect",
                bio="Forward-deployed engineer specializing in production AI systems, multi-tenant RAG architectures, FastAPI microservices, and modern Next.js/React web applications.",
                target_roles=json.dumps([
                    "Forward Deployed Engineer",
                    "AI Solutions Architect",
                    "Full Stack Engineer",
                    "Founding Engineer",
                    "Backend Engineer"
                ]),
                skills=json.dumps([
                    "Python", "FastAPI", "Next.js", "React", "TypeScript",
                    "PostgreSQL", "RAG", "LLM", "Docker", "Vector Search"
                ]),
                negative_keywords=json.dumps([
                    "ios", "swift", "swiftui", "android", "kotlin", "objective-c",
                    "embedded", "firmware", "wordpress", "php", "salesforce"
                ]),
                preferred_locations=json.dumps([
                    "Remote", "Worldwide", "India", "APAC", "Global"
                ]),
                min_salary=0,
                resume_raw_text=""
            )
            db.add(default_profile)
            db.commit()

        ai_cfg = db.query(AIConfig).first()
        if not ai_cfg:
            default_ai = AIConfig(
                id=1,
                provider="gemini",
                api_key="",
                model_name="gemini-2.5-flash",
                ollama_url="http://localhost:11434",
                auto_scan_interval_hours=0,
                enabled_boards=json.dumps([
                    "hn_whoishiring",
                    "hn_freelance",
                    "weworkremotely",
                    "himalayas",
                    "remoteok",
                    "remotive",
                    "jobicy",
                    "arbeitnow",
                    "lever",
                    "ashby"
                ])
            )
            db.add(default_ai)
            db.commit()
    finally:
        db.close()
