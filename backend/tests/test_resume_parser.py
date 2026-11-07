import pytest
from app.services.resume_parser import ResumeParser

def test_resume_parser_heuristic():
    sample_resume = """
    Jane Doe
    jane.doe@example.com | San Francisco, CA

    Summary:
    Forward Deployed Engineer and AI Solutions Architect with 6+ years of production experience building distributed systems.
    
    Technical Skills:
    Languages: Python, TypeScript, JavaScript, Go, SQL
    Frameworks: FastAPI, Next.js, React, Node.js, Django
    AI / Data: RAG, PyTorch, Vector Search, LangChain, PostgreSQL, Docker, AWS
    """

    parsed = ResumeParser.parse_profile_from_text(sample_resume, ai_config=None)
    assert parsed["full_name"] == "Jane Doe"
    assert "Python" in parsed["suggested_skills"]
    assert "FastAPI" in parsed["suggested_skills"]
    assert "Next.js" in parsed["suggested_skills"]
    assert len(parsed["suggested_target_roles"]) > 0

def test_extract_text_empty_pdf_raises():
    with pytest.raises(ValueError, match="empty"):
        ResumeParser.extract_text_from_pdf(b"")

def test_extract_text_corrupted_pdf_raises():
    with pytest.raises(ValueError, match="Could not parse PDF"):
        ResumeParser.extract_text_from_pdf(b"not a valid pdf document")
