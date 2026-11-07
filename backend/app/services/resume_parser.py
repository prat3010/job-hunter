import io
import re
import json
from typing import Dict, Any, Optional
from pypdf import PdfReader
from app.services.llm_gateway import LLMGateway

class ResumeParser:
    """Extracts text from PDF/Text resumes and structures profile attributes."""

    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        if not file_bytes or len(file_bytes.strip()) == 0:
            raise ValueError("Uploaded PDF document is empty (0 bytes).")
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            if getattr(reader, "is_encrypted", False):
                raise ValueError("PDF document is password-protected or encrypted.")
            text_parts = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
            full_text = "\n".join(text_parts).strip()
            if not full_text:
                raise ValueError(
                    "No readable text found in PDF. If this is an image-only scan, "
                    "please provide a text-based PDF or paste your profile directly."
                )
            return full_text
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Could not parse PDF document: {str(e)}")

    @classmethod
    def parse_profile_from_text(cls, raw_text: str, ai_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract structured profile attributes using LLM or regex fallback."""
        if not raw_text:
            return {
                "full_name": "Software Engineer",
                "headline": "Full-Stack Software Engineer",
                "bio": "",
                "suggested_target_roles": ["Full Stack Engineer", "Backend Engineer"],
                "suggested_skills": ["Python", "TypeScript", "React"],
                "suggested_negative_keywords": ["wordpress", "php", "embedded"],
                "raw_text": ""
            }

        # Try LLM extraction if configured
        if ai_config and ai_config.get("api_key"):
            prompt = f"""You are an expert technical recruiter analyzing a candidate's resume text.

Resume Text:
\"\"\"
{raw_text[:5000]}
\"\"\"

Extract the following candidate details and return ONLY a valid JSON object matching this schema:
{{
  "full_name": "Candidate Full Name",
  "headline": "A concise, modern professional headline (e.g. Senior Full-Stack & AI Engineer)",
  "bio": "A 2-3 sentence executive summary of candidate's engineering background and impact",
  "suggested_target_roles": ["Role 1", "Role 2", "Role 3", "Role 4"],
  "suggested_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5", "Skill 6", "Skill 7", "Skill 8"],
  "suggested_negative_keywords": ["unwanted tech 1", "unwanted tech 2"]
}}"""
            llm_res = LLMGateway.generate_text(prompt, ai_config)
            if llm_res:
                try:
                    json_match = re.search(r"(\{.*\})", llm_res, re.DOTALL)
                    raw_json = json_match.group(1) if json_match else llm_res.strip()
                    clean_json = re.sub(r"^```json\s*", "", raw_json.strip())
                    clean_json = re.sub(r"\s*```$", "", clean_json.strip())
                    parsed = json.loads(clean_json)
                    if isinstance(parsed, dict) and "suggested_skills" in parsed:
                        parsed["raw_text"] = raw_text
                        return parsed
                except Exception:
                    pass

        # Robust Heuristic / Regex Fallback
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        first_line = lines[0] if lines else "Candidate"
        name = first_line if len(first_line.split()) <= 4 else "Software Engineer"

        tech_keywords = [
            "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "FastAPI",
            "Django", "Flask", "Go", "Rust", "C++", "Java", "Docker", "Kubernetes", "AWS",
            "GCP", "PostgreSQL", "MySQL", "MongoDB", "Redis", "GraphQL", "Tailwind CSS",
            "PyTorch", "TensorFlow", "RAG", "LLM", "Vector Search", "LangChain", "Celery"
        ]

        found_skills = []
        low_text = raw_text.lower()
        for tech in tech_keywords:
            if re.search(r'\b' + re.escape(tech.lower()) + r'\b', low_text):
                found_skills.append(tech)

        if not found_skills:
            found_skills = ["Python", "TypeScript", "React", "Next.js", "PostgreSQL"]

        return {
            "full_name": name,
            "headline": f"{found_skills[0]} & {found_skills[1] if len(found_skills) > 1 else 'Full-Stack'} Engineer",
            "bio": f"Experienced software engineer with hands-on expertise across {', '.join(found_skills[:5])}.",
            "suggested_target_roles": [
                "Full Stack Engineer",
                "Backend Engineer",
                "AI Solutions Architect",
                "Forward Deployed Engineer"
            ],
            "suggested_skills": found_skills[:12],
            "suggested_negative_keywords": ["wordpress", "php", "embedded", "firmware"],
            "raw_text": raw_text
        }
