import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, init_db
from app.models.job import JobLead

@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    init_db()

@pytest.fixture(autouse=True)
def clean_job_leads():
    # Keep database initialized, only clear job leads between tests
    db = SessionLocal()
    try:
        db.query(JobLead).delete()
        db.commit()
    finally:
        db.close()
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_profile_crud(client):
    # GET profile
    res = client.get("/api/profile")
    assert res.status_code == 200
    data = res.json()
    assert "target_roles" in data
    assert "skills" in data

    # PUT profile
    res = client.put("/api/profile", json={
        "full_name": "Jordan Lee",
        "headline": "Lead AI Solutions Architect",
        "skills": ["Python", "FastAPI", "Next.js", "Docker", "RAG"],
        "target_roles": ["AI Architect", "Founding Engineer"],
        "min_salary": 120000
    })
    assert res.status_code == 200
    updated = res.json()
    assert updated["full_name"] == "Jordan Lee"
    assert "Docker" in updated["skills"]
    assert updated["min_salary"] == 120000

def test_settings_crud(client):
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert "provider" in data
    assert "has_api_key" in data

    # Update settings
    res = client.put("/api/settings", json={
        "provider": "ollama",
        "model_name": "llama3.2",
        "auto_scan_interval_hours": 6
    })
    assert res.status_code == 200
    assert res.json()["provider"] == "ollama"
    assert res.json()["auto_scan_interval_hours"] == 6

def test_jobs_crud_and_pitch(client):
    # Create job lead
    job_payload = {
        "company": "Nexus AI",
        "role": "Senior Full-Stack Engineer",
        "source_url": "https://nexus-ai.example.com/jobs/123",
        "intent_source": "test_board",
        "lead_type": "job",
        "snippet": "Building AI cognitive systems with Python and React.",
        "quality_score": 88,
        "propensity_tier": "A+ High Value"
    }
    res = client.post("/api/jobs", json=job_payload)
    assert res.status_code == 201
    job = res.json()
    job_id = job["id"]
    assert job["company"] == "Nexus AI"
    assert job["status"] == "discovered"

    # List jobs
    res = client.get("/api/jobs")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1

    # Generate pitch
    res = client.post(f"/api/jobs/{job_id}/pitch", json={
        "focus_angle": "RAG architectures"
    })
    assert res.status_code == 200
    pitch = res.json()
    assert "email" in pitch
    assert "linkedin" in pitch
    assert "elevator_pitch" in pitch
    assert len(pitch["linkedin"]) <= 300

    # Verify status changed to pitch_generated
    res = client.get(f"/api/jobs/{job_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "pitch_generated"

    # Update job status to applied
    res = client.patch(f"/api/jobs/{job_id}", json={
        "status": "applied",
        "notes": "Sent cold email via contact form"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "applied"
    assert res.json()["notes"] == "Sent cold email via contact form"

    # Stats
    res = client.get("/api/jobs/stats")
    assert res.status_code == 200
    assert res.json()["counts"]["applied"] == 1

    # Delete job
    res = client.delete(f"/api/jobs/{job_id}")
    assert res.status_code == 204

def test_upload_resume_valid_txt(client):
    resume_content = b"""
    Morgan Vance
    morgan.vance@example.com
    Senior AI Solutions Engineer specializing in FastAPI, Next.js, and RAG systems.
    Skills: Python, TypeScript, React, Docker, PostgreSQL, PyTorch.
    """
    res = client.post(
        "/api/profile/upload-resume",
        files={"file": ("resume.txt", resume_content, "text/plain")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["full_name"] == "Morgan Vance"
    assert "Python" in data["suggested_skills"]
    assert "FastAPI" in data["suggested_skills"]

def test_upload_resume_empty_fails(client):
    res = client.post(
        "/api/profile/upload-resume",
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

def test_upload_resume_corrupt_pdf_fails(client):
    res = client.post(
        "/api/profile/upload-resume",
        files={"file": ("corrupt.pdf", b"%PDF-invalid-binary-junk", "application/pdf")}
    )
    assert res.status_code == 400
    assert "could not parse" in res.json()["detail"].lower() or "pdf" in res.json()["detail"].lower()
