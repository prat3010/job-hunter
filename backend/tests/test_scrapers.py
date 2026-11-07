import pytest
from app.services.scrapers import _process_posting, AVAILABLE_BOARDS, BOARD_SCRAPER_MAP
from app.services.matcher import SemanticProfileMatcher, LeadPropensityModel

def test_available_boards():
    assert len(AVAILABLE_BOARDS) >= 10
    assert "hn_whoishiring" in BOARD_SCRAPER_MAP
    assert "weworkremotely" in BOARD_SCRAPER_MAP
    assert "remoteok" in BOARD_SCRAPER_MAP
    assert "lever" in BOARD_SCRAPER_MAP
    assert "ashby" in BOARD_SCRAPER_MAP

def test_process_posting_pipeline():
    profile = {
        "full_name": "Dev",
        "headline": "AI Engineer",
        "skills": ["Python", "FastAPI", "React", "RAG"],
        "target_roles": ["AI Engineer", "Full Stack Engineer"],
        "negative_keywords": ["wordpress", "php"],
        "preferred_locations": ["Remote", "Worldwide"]
    }
    matcher = SemanticProfileMatcher(profile)
    propensity = LeadPropensityModel()
    known_urls = set()

    # Valid posting
    res = _process_posting(
        company="Cognitive Inc",
        role="Senior AI Engineer (RAG)",
        source_url="https://cognitive.example.com/jobs/1",
        full_text="Cognitive Inc is hiring a Senior AI Engineer. Remote (Worldwide). Tech: Python, FastAPI, RAG vector pipelines. Comp: $150k - $190k / yr.",
        intent_source="test_source",
        known_urls=known_urls,
        matcher=matcher,
        propensity=propensity,
        profile_data=profile,
        min_score=60
    )

    assert res is not None
    assert res["company"] == "Cognitive Inc"
    assert res["quality_score"] >= 60
    assert res["compensation"] is not None
    assert "$150k" in res["compensation"]
    assert res["compensation_inr"] is not None
    assert res["lead_type"] == "job"

    # Excluded duplicate URL
    known_urls.add("https://cognitive.example.com/jobs/1")
    dup_res = _process_posting(
        company="Cognitive Inc",
        role="Senior AI Engineer (RAG)",
        source_url="https://cognitive.example.com/jobs/1",
        full_text="Some text",
        intent_source="test_source",
        known_urls=known_urls,
        matcher=matcher,
        propensity=propensity,
        profile_data=profile,
        min_score=60
    )
    assert dup_res is None

    # Excluded negative tech
    res_neg = _process_posting(
        company="Legacy Web",
        role="WordPress Maintenance",
        source_url="https://legacy.example.com/jobs/2",
        full_text="Maintain WordPress and PHP sites. Remote Worldwide.",
        intent_source="test_source",
        known_urls=known_urls,
        matcher=matcher,
        propensity=propensity,
        profile_data=profile,
        min_score=60
    )
    assert res_neg is None

    # Excluded when below high salary floor and drops below min_score
    profile_high_floor = dict(profile)
    profile_high_floor["min_salary"] = 180000
    res_floor = _process_posting(
        company="Bootstrapped LLC",
        role="Junior Python Helper",
        source_url="https://bootstrapped.example.com/jobs/3",
        full_text="Junior developer needed. Remote worldwide. Python. Comp: $40,000 / yr.",
        intent_source="test_source",
        known_urls=known_urls,
        matcher=matcher,
        propensity=propensity,
        profile_data=profile_high_floor,
        min_score=50
    )
    assert res_floor is None
