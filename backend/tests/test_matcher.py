import pytest
from app.services.matcher import (
    SemanticProfileMatcher, LeadPropensityModel,
    calculate_fit_score, is_eligible_remote,
    detect_lead_type, extract_compensation, format_compensation_with_inr
)

def test_semantic_matcher_similarity():
    profile = {
        "full_name": "Alex Mercer",
        "headline": "Senior Full-Stack & AI Engineer",
        "bio": "Experienced builder in Python, FastAPI, React, Next.js, and RAG vector search.",
        "target_roles": ["AI Engineer", "Full Stack Engineer"],
        "skills": ["Python", "FastAPI", "React", "Next.js", "PostgreSQL", "RAG"],
        "negative_keywords": ["ios", "swift", "wordpress"]
    }
    matcher = SemanticProfileMatcher(profile)
    
    # Positive match
    sim, top_terms = matcher.match(
        "Full Stack AI Engineer",
        "We are looking for a Python and FastAPI engineer to build RAG vector search pipelines with Next.js."
    )
    assert sim > 0.1
    assert len(top_terms) > 0

    # Unrelated job
    sim_unrelated, _ = matcher.match(
        "Mechanical Technician",
        "Operate CNC milling machine on site in factory floor."
    )
    assert sim_unrelated < 0.05

def test_negative_keywords_exclusion():
    profile = {
        "full_name": "Alex Mercer",
        "target_roles": ["Software Engineer"],
        "skills": ["Python", "React"],
        "negative_keywords": ["ios", "swift", "wordpress"]
    }
    matcher = SemanticProfileMatcher(profile)
    propensity = LeadPropensityModel()

    # Contains excluded keyword
    score, tier, reason = calculate_fit_score(
        "iOS Developer with Swift",
        "Build mobile apps with SwiftUI and UIKit.",
        matcher,
        propensity,
        negative_keywords=profile["negative_keywords"],
        target_roles=profile["target_roles"]
    )
    assert score == 0
    assert "Filtered out" in reason

def test_propensity_model():
    propensity = LeadPropensityModel()
    pct, tier = propensity.predict("Senior AI Architect Remote $180k", 0.45)
    assert 0 <= pct <= 100
    assert tier in ["A+ High Value", "B Qualified", "C Low Priority"]

def test_compensation_extraction():
    # USD Range
    text1 = "Salary is $140,000 - $180,000 / yr plus equity."
    comp1 = extract_compensation(text1)
    assert comp1 is not None
    assert "$140,000" in comp1
    norm, inr = format_compensation_with_inr(comp1)
    assert inr is not None
    assert "LPA" in inr or "Cr" in inr

    # Hourly Rate
    text2 = "Rate: $85/hr for 6 months."
    comp2 = extract_compensation(text2)
    assert comp2 is not None
    assert "85" in comp2

def test_remote_eligibility():
    assert is_eligible_remote("Remote (Worldwide) or anywhere") is True
    assert is_eligible_remote("Must reside in US. US Citizen Only.") is False

def test_lead_type_detection():
    assert detect_lead_type("Contract AI Consultant", "Seeking freelancer for 3-month project.") == "client"
    assert detect_lead_type("Full Stack Developer", "Full-time permanent role at fast growing startup.") == "job"

def test_negative_keywords_cleared_empty_list():
    profile = {
        "full_name": "Alex Mercer",
        "target_roles": ["iOS Engineer"],
        "skills": ["Swift", "SwiftUI"],
        "negative_keywords": []  # Explicitly empty
    }
    matcher = SemanticProfileMatcher(profile)
    propensity = LeadPropensityModel()

    score, tier, reason = calculate_fit_score(
        "iOS Engineer (Swift)",
        "Build mobile apps with SwiftUI. Remote worldwide.",
        matcher,
        propensity,
        negative_keywords=[],
        target_roles=["iOS Engineer"]
    )
    # Since negative_keywords is explicitly empty, it must NOT filter out iOS/Swift
    assert score > 0
    assert "Filtered out" not in reason

def test_min_salary_floor_penalty():
    profile = {
        "full_name": "Alex Mercer",
        "target_roles": ["Software Engineer"],
        "skills": ["Python", "React"]
    }
    matcher = SemanticProfileMatcher(profile)
    propensity = LeadPropensityModel()

    # Job paying $60k when candidate's floor is $120k
    score_low, _, reason_low = calculate_fit_score(
        "Python Engineer",
        "Build web services with Python.",
        matcher,
        propensity,
        min_salary=120000,
        compensation_str="$50,000 - $60,000 / yr"
    )
    assert "Below floor" in reason_low

    # Job paying $150k when candidate's floor is $120k
    score_high, _, reason_high = calculate_fit_score(
        "Python Engineer",
        "Build web services with Python.",
        matcher,
        propensity,
        min_salary=120000,
        compensation_str="$140,000 - $160,000 / yr"
    )
    assert "Below floor" not in reason_high
    assert score_high > score_low

def test_hourly_and_monthly_compensation_inr():
    from app.services.matcher import parse_annual_compensation_usd

    # Hourly rate: $85/hr
    norm, inr = format_compensation_with_inr("$85/hr")
    assert "/hr" in inr
    assert "₹7,140" in inr
    ann_min, ann_max = parse_annual_compensation_usd("$85/hr")
    assert ann_min == 170000.0  # 85 * 2000

    # Monthly rate: $5,000 - $8,000 / mo
    norm_mo, inr_mo = format_compensation_with_inr("$5,000 - $8,000 / mo")
    assert "L/mo" in inr_mo
    ann_min_mo, ann_max_mo = parse_annual_compensation_usd("$5,000 - $8,000 / mo")
    assert ann_min_mo == 60000.0  # 5000 * 12
    assert ann_max_mo == 96000.0  # 8000 * 12
