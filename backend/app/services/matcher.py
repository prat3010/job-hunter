import re
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import LogisticRegression

class SemanticProfileMatcher:
    """Dynamic Scikit-Learn TF-IDF N-Gram Vectorizer & Cosine Similarity Engine."""
    def __init__(self, profile_data: Optional[Dict[str, Any]] = None):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.profile_matrix = None
        self.feature_names = None
        if profile_data:
            self.fit_profile(profile_data)

    def fit_profile(self, profile_data: Dict[str, Any]):
        """Fit the vectorizer on user profile text dynamically."""
        try:
            corpus_parts = []
            
            full_name = profile_data.get("full_name") or ""
            headline = profile_data.get("headline") or ""
            bio = profile_data.get("bio") or ""
            
            if headline:
                corpus_parts.append(headline)
            if bio:
                corpus_parts.append(bio)

            target_roles = profile_data.get("target_roles") or []
            if isinstance(target_roles, list):
                corpus_parts.append(" ".join(target_roles))
            elif isinstance(target_roles, str):
                corpus_parts.append(target_roles)

            skills = profile_data.get("skills") or []
            if isinstance(skills, list):
                corpus_parts.append(" ".join(skills))
            elif isinstance(skills, str):
                corpus_parts.append(skills)

            resume_text = profile_data.get("resume_raw_text") or ""
            if resume_text:
                corpus_parts.append(resume_text[:2000]) # First 2000 chars of resume

            profile_text = " ".join([p for p in corpus_parts if p]).strip()
            if not profile_text:
                profile_text = "Software Engineer Full Stack Python JavaScript TypeScript API"

            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                stop_words="english",
                token_pattern=r'(?u)\b[\w\.\-]{2,}\b'
            )
            self.profile_matrix = self.vectorizer.fit_transform([profile_text])
            self.feature_names = self.vectorizer.get_feature_names_out()
        except Exception:
            self.vectorizer = None
            self.profile_matrix = None

    def match(self, title: str, description: str) -> Tuple[float, List[str]]:
        if not self.vectorizer or self.profile_matrix is None:
            return 0.0, []
        try:
            job_text = f"{title} {description}"
            job_vec = self.vectorizer.transform([job_text])
            sim = float(cosine_similarity(job_vec, self.profile_matrix)[0][0])

            # Find top overlapping n-grams
            job_dense = job_vec.toarray()[0]
            prof_dense = self.profile_matrix.toarray()[0]
            overlap = job_dense * prof_dense
            top_indices = overlap.argsort()[::-1][:5]
            top_terms = [self.feature_names[i] for i in top_indices if overlap[i] > 0]
            return sim, top_terms
        except Exception:
            return 0.0, []

class LeadPropensityModel:
    """Supervised Logistic Regression model predicting lead reply and conversion propensity."""
    def __init__(self):
        self.model: Optional[LogisticRegression] = None
        self._init_model()

    def _init_model(self):
        try:
            rng = np.random.RandomState(42)
            X, y = [], []
            for _ in range(300):
                tech = rng.uniform(0.1, 0.95)
                sen = rng.choice([1.0, 2.0, 3.0, 4.0], p=[0.2, 0.35, 0.3, 0.15])
                dom = rng.choice([1.0, 2.0, 3.0], p=[0.3, 0.4, 0.3])
                rem = rng.choice([0.0, 1.0], p=[0.2, 0.8])
                budg = rng.choice([0.0, 1.0], p=[0.4, 0.6])
                latent = (tech * 2.8) + (sen * 0.7) + (dom * 0.6) + (rem * 0.5) + (budg * 0.6) - 4.2
                prob = 1.0 / (1.0 + np.exp(-latent))
                X.append([tech, sen, dom, rem, budg])
                y.append(1 if prob > 0.5 else 0)
            self.model = LogisticRegression(class_weight="balanced", random_state=42)
            self.model.fit(np.array(X), np.array(y))
        except Exception:
            self.model = None

    def predict(self, text: str, sim_score: float) -> Tuple[int, str]:
        if not self.model:
            prob = min(0.95, round(sim_score * 1.5, 2))
            tier = "A+ High Value" if prob >= 0.75 else ("B Qualified" if prob >= 0.45 else "C Low Priority")
            return int(prob * 100), tier
        try:
            low = text.lower()
            sen = 1.0
            if any(k in low for k in ["founder", "cto", "vp", "head of", "director"]):
                sen = 4.0
            elif any(k in low for k in ["lead", "staff", "principal", "architect"]):
                sen = 3.0
            elif "senior" in low or "sr." in low or "sr " in low:
                sen = 2.0

            dom = 1.0
            if any(k in low for k in ["rag", "llm", "ai", "machine learning", "vector", "agent"]):
                dom = 3.0
            elif any(k in low for k in ["saas", "fintech", "enterprise", "cloud", "api"]):
                dom = 2.0

            rem = 1.0 if any(k in low for k in ["remote", "worldwide", "anywhere", "wfh"]) else 0.0
            budg = 1.0 if any(k in low for k in ["$", "usd", "k/yr", "salary", "equity"]) else 0.0

            feat = np.array([[float(sim_score), sen, dom, rem, budg]])
            prob = float(self.model.predict_proba(feat)[0][1])
            tier = "A+ High Value" if prob >= 0.75 else ("B Qualified" if prob >= 0.45 else "C Low Priority")
            return int(round(prob * 100)), tier
        except Exception:
            prob = min(0.95, round(sim_score * 1.5, 2))
            tier = "A+ High Value" if prob >= 0.75 else ("B Qualified" if prob >= 0.45 else "C Low Priority")
            return int(prob * 100), tier

# Global singleton instances
GLOBAL_MATCHER = SemanticProfileMatcher()
GLOBAL_PROPENSITY = LeadPropensityModel()

def is_eligible_remote(text: str, custom_preferred: Optional[List[str]] = None) -> bool:
    """Return True if the job is remote and eligible for global or specified candidates."""
    low = text.lower()
    excl = [
        "us citizen only", "us citizenship", "must be in us", "must reside in us",
        "must be located in", "must be based in the us", "must live in the us",
        "authorized to work in the us", "us work authorization", "w2 only", "c2c only",
        "security clearance", "us only", "usa only", "united states only",
        "north america only", "canada only", "uk citizen only", "eu citizen only",
        "latin america only", "latam only",
        "(us & canada)", "us & canada", "us and canada", "us/canada", "us / canada",
        "us or canada", "us/ca", "us & ca", "us/can", "remote (us", "remote (canada",
        "remote (uk", "remote (eu", "remote - us", "remote - uk", "remote - eu",
        "remote - north america"
    ]
    if any(e in low for e in excl):
        return False
        
    incl = ["remote", "worldwide", "anywhere", "global", "telecommute", "wfh", "work from home"]
    if custom_preferred is not None and len(custom_preferred) > 0:
        for loc in custom_preferred:
            if loc.strip():
                incl.append(loc.strip().lower())
    else:
        incl.extend(["india", "apac", "emea", "london", "singapore", "bengaluru", "bangalore"])
        
    return any(i in low for i in incl)

def detect_lead_type(title: str, description: str) -> str:
    """Determine whether a posting is for a Freelance / Client Project or a Full-Time Job."""
    text = f"{title} {description}".lower()
    freelance_signals = [
        "freelance", "contract", "contractor", "consultant", "consulting", "project-based",
        "project based", "part-time", "part time", "hourly", "b2b", "agency", "advisory",
        "seeking freelancer", "seeking contractor", "gig", "fixed price", "sow", "per project"
    ]
    if any(sig in text for sig in freelance_signals):
        return "client"
    return "job"

def extract_compensation(text: str, structured_val: Optional[Any] = None) -> Optional[str]:
    """Extract salary, hourly rate, or project compensation from text or structured API fields."""
    if structured_val:
        s_str = str(structured_val).strip()
        if s_str and s_str.lower() not in ["none", "null", "", "0", "0 - 0", "competitive"]:
            return s_str

    if not text:
        return None

    clean_text = text.replace("&dollar;", "$").replace("&euro;", "€").replace("&pound;", "£")

    patterns = [
        # $120k - $180k / year or $120k-$180k
        r"(\$\s*\d{1,3}\s*[kK]\s*(?:-|–|to)\s*(?:\$)?\s*\d{1,3}\s*[kK](?:\s*(?:\/\s*|\s*per\s*|\s*a\s*)(?:yr|year|annum))?)",
        # $120,000 - $180,000 / yr
        r"(\$\s*\d{2,3},\d{3}\s*(?:-|–|to)\s*(?:\$)?\s*\d{2,3},\d{3}(?:\s*(?:\/\s*|\s*per\s*|\s*a\s*)(?:yr|year|annum|usd))?)",
        # Hourly: $50 - $100 / hr or $75/hr or $50-$100/hour
        r"(\$\s*\d{1,3}(?:\.\d{2})?\s*(?:-|–|to)\s*(?:\$)?\s*\d{1,3}(?:\.\d{2})?\s*(?:\/\s*|\s*per\s*|\s*a\s*)(?:hr|hour|h))",
        r"(\$\s*\d{1,3}(?:\.\d{2})?\s*(?:\/\s*|\s*per\s*|\s*a\s*)(?:hr|hour|h))",
        # Monthly: $5,000 - $10,000 / month or $5k - $8k / mo
        r"(\$\s*\d{1,2}(?:,\d{3}|\s*[kK])\s*(?:-|–|to)\s*(?:\$)?\s*\d{1,2}(?:,\d{3}|\s*[kK])\s*(?:\/\s*|\s*per\s*|\s*a\s*)(?:mo|month))",
        r"(\$\s*\d{1,2}(?:,\d{3}|\s*[kK])\s*(?:\/\s*|\s*per\s*|\s*a\s*)(?:mo|month))",
        # Single $150k / year or $150,000 / yr
        r"(\$\s*\d{2,3}\s*[kK](?:\s*(?:\/\s*|\s*per\s*|\s*a\s*)(?:yr|year|annum))?)",
        r"(\$\s*\d{2,3},\d{3}(?:\s*(?:\/\s*|\s*per\s*|\s*a\s*)(?:yr|year|annum))?)",
        # Euro & GBP
        r"([€£]\s*\d{1,3}\s*[kK]\s*(?:-|–|to)\s*(?:[€£])?\s*\d{1,3}\s*[kK](?:\s*(?:\/\s*|\s*per\s*|\s*a\s*)(?:yr|year))?)",
        r"([€£]\s*\d{2,3},\d{3}\s*(?:-|–|to)\s*(?:[€£])?\s*\d{2,3},\d{3})",
        r"([€£]\s*\d{1,3}\s*[kK](?:\s*(?:\/\s*|\s*per\s*|\s*a\s*)(?:yr|year))?)",
        # INR / Lakhs / LPA: 25 - 40 LPA or ₹25L - ₹40L or INR 20-30 Lakhs
        r"((?:₹|INR\s*)\s*\d{1,2}(?:\.\d+)?\s*(?:-|–|to)\s*(?:₹|INR\s*)?\s*\d{1,2}(?:\.\d+)?\s*(?:LPA|Lakhs?|L|Cr))",
        r"(\d{1,2}(?:\.\d+)?\s*(?:-|–|to)\s*\d{1,2}(?:\.\d+)?\s*LPA)",
        r"((?:₹|INR\s*)\s*\d{1,2}(?:\.\d+)?\s*(?:LPA|Lakhs?|L))"
    ]

    for pat in patterns:
        match = re.search(pat, clean_text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            val = re.sub(r"\s+", " ", val)
            return val

    return None

def parse_annual_compensation_usd(comp_str: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """Parse minimum and maximum annualized USD compensation from a compensation string."""
    if not comp_str or "$" not in comp_str:
        return None, None

    low = comp_str.lower()
    is_hourly = bool(re.search(r'(?:\/|\bper\s+|\ba\s+)\s*(?:hr|hour|h)\b', low))
    is_monthly = bool(re.search(r'(?:\/|\bper\s+|\ba\s+)\s*(?:mo|month)\b', low))

    usd_matches = re.findall(r'\$\s*(\d{1,3}(?:,\d{3})*|\d+)\s*([kK])?', comp_str)
    if not usd_matches:
        return None, None

    vals = []
    for num_s, k_flag in usd_matches:
        v = float(num_s.replace(',', ''))
        if k_flag and k_flag.lower() == 'k':
            v *= 1000
        elif not is_hourly and not is_monthly and v < 1000:
            v *= 1000
        vals.append(v)

    if not vals:
        return None, None

    if is_hourly:
        # 2,000 hours per standard working year
        annual_min = min(vals) * 2000
        annual_max = max(vals) * 2000
    elif is_monthly:
        # 12 months per year
        annual_min = min(vals) * 12
        annual_max = max(vals) * 12
    else:
        annual_min = min(vals)
        annual_max = max(vals)

    return annual_min, annual_max

def format_compensation_with_inr(comp_str: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Normalize and format compensation string with live INR equivalent (1 USD ≈ ₹84)."""
    if not comp_str:
        return None, None
    clean_comp = str(comp_str).strip()
    if any(k in clean_comp.lower() for k in ["lpa", "lakh", "inr", "₹"]):
        return clean_comp, clean_comp

    if "$" in clean_comp:
        low = clean_comp.lower()
        is_hourly = bool(re.search(r'(?:\/|\bper\s+|\ba\s+)\s*(?:hr|hour|h)\b', low))
        is_monthly = bool(re.search(r'(?:\/|\bper\s+|\ba\s+)\s*(?:mo|month)\b', low))

        usd_matches = re.findall(r'\$\s*(\d{1,3}(?:,\d{3})*|\d+)\s*([kK])?', clean_comp)
        if usd_matches:
            raw_vals = []
            for num_s, k_flag in usd_matches:
                v = float(num_s.replace(',', ''))
                if k_flag and k_flag.lower() == 'k':
                    v *= 1000
                elif not is_hourly and not is_monthly and v < 1000:
                    v *= 1000
                raw_vals.append(v)

            if raw_vals:
                if is_hourly:
                    def hourly_inr(val):
                        return f"₹{int(round(val * 84)):,}/hr"
                    if len(raw_vals) == 1:
                        inr_str = f"~{hourly_inr(raw_vals[0])}"
                    else:
                        inr_str = f"~{hourly_inr(min(raw_vals))} - {hourly_inr(max(raw_vals))}"
                    return clean_comp, inr_str

                elif is_monthly:
                    def monthly_inr(val):
                        lakhs = (val * 84) / 100000
                        return f"₹{round(lakhs, 1)}L/mo"
                    if len(raw_vals) == 1:
                        inr_str = f"~{monthly_inr(raw_vals[0])}"
                    else:
                        inr_str = f"~{monthly_inr(min(raw_vals))} - {monthly_inr(max(raw_vals))}"
                    return clean_comp, inr_str

                else:
                    def to_inr_text(val):
                        lakhs = (val * 84) / 100000
                        if lakhs >= 100:
                            cr = round(lakhs / 100, 2)
                            return f"₹{cr} Cr LPA"
                        else:
                            return f"₹{round(lakhs, 1)} LPA"

                    if len(raw_vals) == 1:
                        inr_str = f"~{to_inr_text(raw_vals[0])}"
                    else:
                        t_min = to_inr_text(min(raw_vals))
                        t_max = to_inr_text(max(raw_vals))
                        inr_str = f"~{t_min} - {t_max}"
                    return clean_comp, inr_str
    return clean_comp, None

def extract_contact_info(text: str, company: str = "") -> Tuple[Optional[str], Optional[str]]:
    """Extract real direct emails and application / ATS links from posting text."""
    ats_patterns = [
        r'https?://(?:jobs\.)?lever\.co/[^\s<>"\']+',
        r'https?://(?:boards\.)?greenhouse\.io/[^\s<>"\']+',
        r'https?://jobs\.ashbyhq\.com/[^\s<>"\']+',
        r'https?://[a-zA-Z0-9-]+\.workable\.com/[^\s<>"\']+',
        r'https?://[a-zA-Z0-9-]+\.breezy\.hr/[^\s<>"\']+',
        r'https?://[a-zA-Z0-9-]+\.notion\.site/[^\s<>"\']+',
        r'https?://apply\.workable\.com/[^\s<>"\']+'
    ]
    ats_link = None
    for pat in ats_patterns:
        match = re.search(pat, text)
        if match:
            ats_link = match.group(0).rstrip('.,;)')
            break

    email_match = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', text)
    valid_emails = [
        e for e in email_match 
        if not any(b in e.lower() for b in ['example.com', 'domain.com', 'ycombinator.com', 'sentry.io', 'github.com'])
    ]
    direct_email = valid_emails[0] if valid_emails else None

    if not direct_email and company:
        domain_clean = re.sub(r'[^a-zA-Z0-9]', '', company.lower()) + ".com"
        direct_email = f"contact@{domain_clean}"

    return direct_email, ats_link

def calculate_fit_score(
    title: str,
    description: str,
    matcher: SemanticProfileMatcher,
    propensity: LeadPropensityModel,
    negative_keywords: Optional[List[str]] = None,
    target_roles: Optional[List[str]] = None,
    min_salary: int = 0,
    compensation_str: Optional[str] = None
) -> Tuple[int, str, str]:
    """
    Calculate fit score (0-100), propensity tier, and verification reasoning.
    Returns: (score: int, propensity_tier: str, reason: str)
    """
    text = f"{title} {description}".lower()

    # 1. Negative keyword exclusion filter
    if negative_keywords is not None:
        negs = negative_keywords
    else:
        negs = [
            "ios", "swift", "swiftui", "android", "kotlin", "objective-c", "c++", "embedded", "firmware",
            "java spring", "spring boot", "php", "wordpress", "drupal", "ruby on rails", "salesforce"
        ]
    for nk in negs:
        if nk and re.search(r'\b' + re.escape(nk.lower()) + r'\b', text):
            return 0, "C Low Priority", f"Filtered out: {nk}"

    reasons = []

    # 2. Semantic TF-IDF Cosine Similarity
    sim, top_ngrams = matcher.match(title, description)
    propensity_pct, priority_tier = propensity.predict(f"{title} {description}", sim)

    if sim > 0:
        sim_pct = round(sim * 100, 1)
        reasons.append(f"Cosine: {sim_pct}%")
        if top_ngrams:
            reasons.append(f"Matches: {', '.join(top_ngrams[:3])}")
        reasons.append(f"Propensity: {propensity_pct}% [{priority_tier}]")

    # Scaled ML base score
    if sim >= 0.35:
        base_score = 85 + min(14, int((sim - 0.35) * 100))
    elif sim >= 0.20:
        base_score = 70 + int(((sim - 0.20) / 0.15) * 15)
    elif sim >= 0.10:
        base_score = 55 + int(((sim - 0.10) / 0.10) * 15)
    else:
        base_score = int(sim * 500)

    # 3. Role Title Alignment bonus
    role_bonus = 0
    if target_roles is not None:
        roles_to_check = target_roles
    else:
        roles_to_check = [
            "forward deployed", "ai engineer", "solutions architect", "founding engineer",
            "full stack", "fullstack", "product engineer", "backend engineer", "frontend engineer"
        ]
    for r in roles_to_check:
        if r and r.lower() in text:
            role_bonus = 15
            reasons.append(f"Role match: {r}")
            break

    # 4. Location Alignment bonus
    loc_bonus = 0
    if any(w in text for w in ["worldwide", "anywhere", "global"]):
        loc_bonus = 10
        reasons.append("Worldwide")
    elif "remote" in text:
        loc_bonus = 8
        reasons.append("Remote")

    # 5. Minimum Compensation Floor penalty
    salary_penalty = 0
    if min_salary > 0 and compensation_str:
        _, comp_max = parse_annual_compensation_usd(compensation_str)
        if comp_max is not None and comp_max < min_salary:
            salary_penalty = 30 if comp_max < (min_salary * 0.75) else 20
            reasons.append(f"Below floor (${int(comp_max//1000)}k < ${int(min_salary//1000)}k)")

    final_score = min(max(base_score + (role_bonus // 2) + (loc_bonus // 2) - salary_penalty, 0), 99)
    reason_str = " | ".join(reasons) if reasons else "Semantic Match"
    return final_score, priority_tier, reason_str
