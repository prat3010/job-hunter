import re
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Set, Optional, Callable

from app.services.matcher import (
    SemanticProfileMatcher, LeadPropensityModel,
    is_eligible_remote, detect_lead_type, extract_compensation,
    format_compensation_with_inr, extract_contact_info, calculate_fit_score
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/xml, application/xml, */*"
}

AVAILABLE_BOARDS = [
    {"id": "hn_whoishiring", "name": "Hacker News (Who is Hiring)"},
    {"id": "hn_freelance", "name": "Hacker News (Freelance / Gigs)"},
    {"id": "weworkremotely", "name": "WeWorkRemotely"},
    {"id": "himalayas", "name": "Himalayas RSS"},
    {"id": "remoteok", "name": "RemoteOK"},
    {"id": "remotive", "name": "Remotive API"},
    {"id": "jobicy", "name": "Jobicy Remote"},
    {"id": "arbeitnow", "name": "Arbeitnow"},
    {"id": "lever", "name": "Lever ATS Boards"},
    {"id": "ashby", "name": "Ashby ATS Boards"},
    {"id": "greenhouse", "name": "Greenhouse ATS Boards"},
]

def _process_posting(
    company: str,
    role: str,
    source_url: str,
    full_text: str,
    intent_source: str,
    known_urls: Set[str],
    matcher: SemanticProfileMatcher,
    propensity: LeadPropensityModel,
    profile_data: Dict[str, Any],
    min_score: int,
    structured_comp: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    if not source_url or source_url in known_urls:
        return None

    pref_locs = profile_data.get("preferred_locations", None)
    if not is_eligible_remote(full_text, pref_locs):
        return None

    negs = profile_data.get("negative_keywords", None)
    target_roles = profile_data.get("target_roles", None)
    min_salary = profile_data.get("min_salary", 0)

    comp_raw = extract_compensation(full_text, structured_comp)
    comp_norm, comp_inr = format_compensation_with_inr(comp_raw)
    
    score, tier, reason = calculate_fit_score(
        role, full_text, matcher, propensity, negs, target_roles, min_salary, comp_raw
    )

    if score < min_score:
        return None

    direct_email, ats_link = extract_contact_info(full_text, company)
    lead_type = detect_lead_type(role, full_text)

    clean_snippet = full_text[:600].strip()

    return {
        "company": company.strip() or "Tech Company",
        "role": role.strip() or "Software Engineer",
        "source_url": ats_link or source_url,
        "snippet": clean_snippet,
        "description": full_text[:4000],
        "email": direct_email,
        "compensation": comp_norm,
        "compensation_inr": comp_inr,
        "quality_score": score,
        "propensity_tier": tier,
        "verification_reason": reason,
        "intent_source": intent_source,
        "lead_type": lead_type
    }

def fetch_hn_whoishiring(known_urls: Set[str], profile_data: Dict[str, Any], min_score: int = 65) -> List[Dict[str, Any]]:
    results = []
    matcher = SemanticProfileMatcher(profile_data)
    propensity = LeadPropensityModel()
    
    try:
        user_url = 'https://hacker-news.firebaseio.com/v0/user/whoishiring.json'
        req = urllib.request.Request(user_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as resp:
            user_data = json.loads(resp.read().decode('utf-8'))
        
        thread_id = None
        for tid in user_data.get('submitted', [])[:5]:
            item_url = f'https://hacker-news.firebaseio.com/v0/item/{tid}.json'
            with urllib.request.urlopen(urllib.request.Request(item_url, headers=HEADERS), timeout=4) as r:
                tdata = json.loads(r.read().decode('utf-8'))
            if 'who is hiring' in tdata.get('title', '').lower():
                thread_id = tid
                break
                
        if not thread_id:
            return results

        item_url = f'https://hacker-news.firebaseio.com/v0/item/{thread_id}.json'
        with urllib.request.urlopen(urllib.request.Request(item_url, headers=HEADERS), timeout=4) as r:
            tdata = json.loads(r.read().decode('utf-8'))
        kids = tdata.get('kids', [])[:100]

        def fetch_comment(cid):
            try:
                kurl = f'https://hacker-news.firebaseio.com/v0/item/{cid}.json'
                with urllib.request.urlopen(urllib.request.Request(kurl, headers=HEADERS), timeout=3) as kr:
                    return json.loads(kr.read().decode('utf-8'))
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=12) as executor:
            comments = list(executor.map(fetch_comment, kids))

        for c in comments:
            if not c:
                continue
            cid = c.get('id')
            source_url = f'https://news.ycombinator.com/item?id={cid}'
            raw_text = c.get('text') or ''
            if not raw_text:
                continue
            clean_text = re.sub(r'<[^>]+>', ' ', raw_text).strip()
            lines = [l.strip() for l in clean_text.split('\n') if l.strip()]
            first_line = lines[0] if lines else clean_text[:100]

            parts = [p.strip() for p in first_line.split('|')]
            company = parts[0] if len(parts) > 0 else 'Startup'
            role = parts[1] if len(parts) > 1 else 'Remote Software Engineer'

            item = _process_posting(
                company=company,
                role=role,
                source_url=source_url,
                full_text=clean_text,
                intent_source="hn_whoishiring",
                known_urls=known_urls,
                matcher=matcher,
                propensity=propensity,
                profile_data=profile_data,
                min_score=min_score
            )
            if item:
                results.append(item)
    except Exception:
        pass
    return results

def fetch_hn_freelance(known_urls: Set[str], profile_data: Dict[str, Any], min_score: int = 65) -> List[Dict[str, Any]]:
    results = []
    matcher = SemanticProfileMatcher(profile_data)
    propensity = LeadPropensityModel()
    queries = ['"seeking freelancer"', '"seeking contractor"', '"contract" AND "python"', '"freelance" AND "ai"']
    
    try:
        for q in queries:
            url = f'https://hn.algolia.com/api/v1/search_by_date?query={urllib.parse.quote(q)}&tags=comment&hitsPerPage=10'
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            hits = data.get('hits', [])
            for h in hits:
                cid = h.get('objectID')
                source_url = f'https://news.ycombinator.com/item?id={cid}'
                raw_text = h.get('comment_text', '')
                clean_text = re.sub(r'<[^>]+>', ' ', raw_text).strip()
                author = h.get('author', 'HN Client')

                item = _process_posting(
                    company=f"Client: @{author}",
                    role="Freelance / Contract Engineer",
                    source_url=source_url,
                    full_text=clean_text,
                    intent_source="hn_freelance",
                    known_urls=known_urls,
                    matcher=matcher,
                    propensity=propensity,
                    profile_data=profile_data,
                    min_score=min_score
                )
                if item:
                    item["lead_type"] = "client"
                    results.append(item)
    except Exception:
        pass
    return results

def fetch_weworkremotely(known_urls: Set[str], profile_data: Dict[str, Any], min_score: int = 65) -> List[Dict[str, Any]]:
    results = []
    matcher = SemanticProfileMatcher(profile_data)
    propensity = LeadPropensityModel()
    
    try:
        url = 'https://weworkremotely.com/categories/remote-programming-jobs.rss'
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as resp:
            root = ET.fromstring(resp.read())

        for item in root.findall('.//item')[:40]:
            title = item.find('title').text or ''
            link = item.find('link').text or ''
            desc = item.find('description').text or title
            clean_desc = re.sub(r'<[^>]+>', ' ', desc).strip()

            if ':' in title:
                company, role = title.split(':', 1)
            else:
                company, role = title, 'Remote Developer'

            posting = _process_posting(
                company=company,
                role=role,
                source_url=link,
                full_text=f"{role} at {company}. {clean_desc}",
                intent_source="weworkremotely",
                known_urls=known_urls,
                matcher=matcher,
                propensity=propensity,
                profile_data=profile_data,
                min_score=min_score
            )
            if posting:
                results.append(posting)
    except Exception:
        pass
    return results

def fetch_himalayas(known_urls: Set[str], profile_data: Dict[str, Any], min_score: int = 65) -> List[Dict[str, Any]]:
    results = []
    matcher = SemanticProfileMatcher(profile_data)
    propensity = LeadPropensityModel()

    try:
        url = 'https://himalayas.app/jobs/rss'
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as resp:
            root = ET.fromstring(resp.read())

        for item in root.findall('.//item')[:50]:
            title = item.find('title').text or ''
            link = item.find('link').text or ''
            desc = item.find('description').text or title
            clean_desc = re.sub(r'<[^>]+>', ' ', desc).strip()

            company = "Tech Startup"
            role = title
            if " at " in title:
                parts = title.split(" at ", 1)
                role, company = parts[0], parts[1]

            posting = _process_posting(
                company=company,
                role=role,
                source_url=link,
                full_text=f"{role} at {company}. {clean_desc}",
                intent_source="himalayas",
                known_urls=known_urls,
                matcher=matcher,
                propensity=propensity,
                profile_data=profile_data,
                min_score=min_score
            )
            if posting:
                results.append(posting)
    except Exception:
        pass
    return results

def fetch_remoteok(known_urls: Set[str], profile_data: Dict[str, Any], min_score: int = 65) -> List[Dict[str, Any]]:
    results = []
    matcher = SemanticProfileMatcher(profile_data)
    propensity = LeadPropensityModel()

    try:
        url = 'https://remoteok.com/api'
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            jobs = json.loads(resp.read().decode('utf-8'))

        for job in jobs[1:45]:
            if not isinstance(job, dict):
                continue
            link = job.get('url') or f"https://remoteok.com/remote-jobs/{job.get('id')}"
            company = job.get('company', 'Tech Startup')
            role = job.get('position', 'Remote Developer')
            description = job.get('description', '')
            tags = " ".join(job.get('tags', []))
            full_text = f"{role} at {company}. {tags} {description}"
            clean_desc = re.sub(r'<[^>]+>', ' ', full_text).strip()

            s_min = job.get('salary_min')
            s_max = job.get('salary_max')
            structured_comp = None
            if s_min and s_max and s_max > 0:
                structured_comp = f"${s_min:,} - ${s_max:,} / yr"
            elif job.get('salary'):
                structured_comp = str(job.get('salary'))

            posting = _process_posting(
                company=company,
                role=role,
                source_url=job.get('apply_url') or link,
                full_text=clean_desc,
                intent_source="remoteok",
                known_urls=known_urls,
                matcher=matcher,
                propensity=propensity,
                profile_data=profile_data,
                min_score=min_score,
                structured_comp=structured_comp
            )
            if posting:
                results.append(posting)
    except Exception:
        pass
    return results

def fetch_remotive(known_urls: Set[str], profile_data: Dict[str, Any], min_score: int = 65) -> List[Dict[str, Any]]:
    results = []
    matcher = SemanticProfileMatcher(profile_data)
    propensity = LeadPropensityModel()

    try:
        url = 'https://remotive.com/api/remote-jobs?category=software-dev'
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            jobs = data.get('jobs', [])

        for job in jobs[:40]:
            link = job.get('url', '')
            company = job.get('company_name', 'Tech Startup')
            role = job.get('title', 'Remote Developer')
            desc = job.get('description', '')
            clean_desc = re.sub(r'<[^>]+>', ' ', desc).strip()
            full_text = f"{role} at {company}. {clean_desc}"

            posting = _process_posting(
                company=company,
                role=role,
                source_url=link,
                full_text=full_text,
                intent_source="remotive",
                known_urls=known_urls,
                matcher=matcher,
                propensity=propensity,
                profile_data=profile_data,
                min_score=min_score,
                structured_comp=job.get('salary')
            )
            if posting:
                results.append(posting)
    except Exception:
        pass
    return results

def fetch_jobicy(known_urls: Set[str], profile_data: Dict[str, Any], min_score: int = 65) -> List[Dict[str, Any]]:
    results = []
    matcher = SemanticProfileMatcher(profile_data)
    propensity = LeadPropensityModel()

    try:
        url = 'https://jobicy.com/api/v2/remote-jobs?count=35&industry=engineering'
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            jobs = data.get('jobs', [])

        for job in jobs:
            link = job.get('url', '')
            company = job.get('companyName', 'Tech Startup')
            role = job.get('jobTitle', 'Remote Developer')
            desc = job.get('jobDescription', '')
            clean_desc = re.sub(r'<[^>]+>', ' ', desc).strip()
            full_text = f"{role} at {company}. {clean_desc}"

            s_min = job.get('annualSalaryMin')
            s_max = job.get('annualSalaryMax')
            structured_comp = f"${int(s_min):,} - ${int(s_max):,} USD / yr" if (s_min and s_max) else None

            posting = _process_posting(
                company=company,
                role=role,
                source_url=link,
                full_text=full_text,
                intent_source="jobicy",
                known_urls=known_urls,
                matcher=matcher,
                propensity=propensity,
                profile_data=profile_data,
                min_score=min_score,
                structured_comp=structured_comp
            )
            if posting:
                results.append(posting)
    except Exception:
        pass
    return results

def fetch_arbeitnow(known_urls: Set[str], profile_data: Dict[str, Any], min_score: int = 65) -> List[Dict[str, Any]]:
    results = []
    matcher = SemanticProfileMatcher(profile_data)
    propensity = LeadPropensityModel()

    try:
        url = 'https://www.arbeitnow.com/api/job-board-api'
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            jobs = data.get('data', [])

        for job in jobs[:35]:
            if not job.get('remote'):
                continue
            link = job.get('url', '')
            company = job.get('company_name', 'Tech Startup')
            role = job.get('title', 'Remote Developer')
            desc = job.get('description', '')
            clean_desc = re.sub(r'<[^>]+>', ' ', desc).strip()
            full_text = f"{role} at {company}. {clean_desc}"

            posting = _process_posting(
                company=company,
                role=role,
                source_url=link,
                full_text=full_text,
                intent_source="arbeitnow",
                known_urls=known_urls,
                matcher=matcher,
                propensity=propensity,
                profile_data=profile_data,
                min_score=min_score,
                structured_comp=job.get('salary')
            )
            if posting:
                results.append(posting)
    except Exception:
        pass
    return results

def fetch_lever_boards(known_urls: Set[str], profile_data: Dict[str, Any], min_score: int = 65) -> List[Dict[str, Any]]:
    results = []
    matcher = SemanticProfileMatcher(profile_data)
    propensity = LeadPropensityModel()
    lever_companies = ['palantir', 'spotify', 'wealthfront', 'canva', 'atlassian', 'netflix']

    def check_lever(slug):
        sub = []
        try:
            url = f'https://api.lever.co/v0/postings/{slug}?mode=json'
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                jobs = json.loads(resp.read().decode('utf-8'))
            for j in jobs[:20]:
                link = j.get('hostedUrl', '') or j.get('applyUrl', '')
                title = j.get('text', '')
                cats = j.get('categories', {})
                loc = str(cats.get('location', ''))
                team = str(cats.get('team', ''))
                desc = j.get('descriptionPlain', '') or ''
                full_text = f"{title} at {slug.capitalize()} ({loc}) - {team}\n{desc}"

                posting = _process_posting(
                    company=slug.capitalize(),
                    role=title,
                    source_url=link,
                    full_text=full_text,
                    intent_source=f"lever_{slug}",
                    known_urls=known_urls,
                    matcher=matcher,
                    propensity=propensity,
                    profile_data=profile_data,
                    min_score=min_score
                )
                if posting:
                    sub.append(posting)
        except Exception:
            pass
        return sub

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(check_lever, s) for s in lever_companies]
        for f in futures:
            results.extend(f.result())
    return results

def fetch_ashby_boards(known_urls: Set[str], profile_data: Dict[str, Any], min_score: int = 65) -> List[Dict[str, Any]]:
    results = []
    matcher = SemanticProfileMatcher(profile_data)
    propensity = LeadPropensityModel()
    ashby_companies = [
        'linear', 'vercel', 'langchain', 'perplexity', 'together', 'modal',
        'elevenlabs', 'anyscale', 'cursor', 'cohere', 'replit', 'groq', 'pinecone'
    ]

    def check_ashby(slug):
        sub = []
        try:
            url = f'https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true'
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            for j in data.get('jobs', [])[:20]:
                link = j.get('jobUrl', '')
                title = j.get('title', '')
                loc = str(j.get('location', ''))
                comp_data = j.get('compensation', {})
                comp_str = comp_data.get('compensationTierSummary') if isinstance(comp_data, dict) else None
                full_text = f"{title} at {slug.capitalize()} ({loc}) Comp: {comp_str}"

                posting = _process_posting(
                    company=slug.capitalize(),
                    role=title,
                    source_url=link,
                    full_text=full_text,
                    intent_source=f"ashby_{slug}",
                    known_urls=known_urls,
                    matcher=matcher,
                    propensity=propensity,
                    profile_data=profile_data,
                    min_score=min_score,
                    structured_comp=comp_str
                )
                if posting:
                    sub.append(posting)
        except Exception:
            pass
        return sub

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(check_ashby, s) for s in ashby_companies]
        for f in futures:
            results.extend(f.result())
    return results

def fetch_greenhouse_boards(known_urls: Set[str], profile_data: Dict[str, Any], min_score: int = 65) -> List[Dict[str, Any]]:
    results = []
    matcher = SemanticProfileMatcher(profile_data)
    propensity = LeadPropensityModel()
    gh_companies = ['gitlab', 'sourcegraph', 'sentry', 'retool', 'cloudflare', 'supabase', 'stripe']

    def check_gh(slug):
        sub = []
        try:
            url = f'https://boards-api.greenhouse.io/v1/boards/{slug}/jobs'
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            for j in data.get('jobs', [])[:20]:
                link = j.get('absolute_url', '')
                title = j.get('title') or ''
                loc = (j.get('location') or {}).get('name') or ''
                full_text = f"{title} at {slug.capitalize()} ({loc})"

                posting = _process_posting(
                    company=slug.capitalize(),
                    role=title,
                    source_url=link,
                    full_text=full_text,
                    intent_source=f"gh_{slug}",
                    known_urls=known_urls,
                    matcher=matcher,
                    propensity=propensity,
                    profile_data=profile_data,
                    min_score=min_score
                )
                if posting:
                    sub.append(posting)
        except Exception:
            pass
        return sub

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(check_gh, s) for s in gh_companies]
        for f in futures:
            results.extend(f.result())
    return results

BOARD_SCRAPER_MAP = {
    "hn_whoishiring": ("Hacker News (Who is Hiring)", fetch_hn_whoishiring),
    "hn_freelance": ("Hacker News (Freelance)", fetch_hn_freelance),
    "weworkremotely": ("WeWorkRemotely", fetch_weworkremotely),
    "himalayas": ("Himalayas RSS", fetch_himalayas),
    "remoteok": ("RemoteOK", fetch_remoteok),
    "remotive": ("Remotive API", fetch_remotive),
    "jobicy": ("Jobicy Remote", fetch_jobicy),
    "arbeitnow": ("Arbeitnow", fetch_arbeitnow),
    "lever": ("Lever ATS", fetch_lever_boards),
    "ashby": ("Ashby ATS", fetch_ashby_boards),
    "greenhouse": ("Greenhouse ATS", fetch_greenhouse_boards),
}

def run_scanners(
    board_ids: Optional[List[str]],
    known_urls: Set[str],
    profile_data: Dict[str, Any],
    min_score: int = 65,
    progress_callback: Optional[Callable[[str, str, str, int, Optional[str]], None]] = None
) -> List[Dict[str, Any]]:
    """
    Run selected scrapers with optional progress callbacks.
    progress_callback(board_id, name, status, found_count, error)
    """
    selected_ids = board_ids if board_ids else list(BOARD_SCRAPER_MAP.keys())
    all_discovered = []

    for bid in selected_ids:
        if bid not in BOARD_SCRAPER_MAP:
            continue
        name, scraper_func = BOARD_SCRAPER_MAP[bid]
        if progress_callback:
            progress_callback(bid, name, "scanning", 0, None)
        try:
            leads = scraper_func(known_urls, profile_data, min_score)
            all_discovered.extend(leads)
            if progress_callback:
                progress_callback(bid, name, "completed", len(leads), None)
        except Exception as e:
            if progress_callback:
                progress_callback(bid, name, "failed", 0, str(e))

    return all_discovered
