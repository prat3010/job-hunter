import json
import re
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

class LLMGateway:
    """Multi-Provider BYOK Client supporting Gemini, OpenAI, Anthropic, Groq, and Local Ollama."""

    @staticmethod
    def call_gemini(prompt: str, api_key: str, model: str = "gemini-2.5-flash") -> Optional[str]:
        if not api_key:
            return None
        models = [model, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        seen = set()
        ordered = [m for m in models if not (m in seen or seen.add(m))]

        for m in ordered:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
                payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    text = res.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if text:
                        return text.strip()
            except Exception:
                pass
        return None

    @staticmethod
    def call_openai_compatible(prompt: str, api_key: str, base_url: str, model: str) -> Optional[str]:
        if not api_key:
            return None
        try:
            url = f"{base_url.rstrip('/')}/chat/completions"
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                text = res.get("choices", [{}])[0].get("message", {}).get("content", "")
                if text:
                    return text.strip()
        except Exception:
            pass
        return None

    @staticmethod
    def call_anthropic(prompt: str, api_key: str, model: str = "claude-3-5-haiku-20241022") -> Optional[str]:
        if not api_key:
            return None
        try:
            url = "https://api.anthropic.com/v1/messages"
            payload = json.dumps({
                "model": model,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}]
            }).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                parts = res.get("content", [])
                text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
                if text:
                    return text.strip()
        except Exception:
            pass
        return None

    @staticmethod
    def call_ollama(prompt: str, ollama_url: str = "http://localhost:11434", model: str = "llama3.2") -> Optional[str]:
        try:
            url = f"{ollama_url.rstrip('/')}/api/generate"
            payload = json.dumps({
                "model": model,
                "prompt": prompt,
                "stream": False
            }).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                text = res.get("response", "")
                if text:
                    return text.strip()
        except Exception:
            pass
        return None

    @classmethod
    def generate_text(cls, prompt: str, ai_config: Dict[str, Any]) -> Optional[str]:
        provider = (ai_config.get("provider") or "gemini").lower()
        api_key = ai_config.get("api_key") or ""
        model = ai_config.get("model_name") or "gemini-2.5-flash"
        ollama_url = ai_config.get("ollama_url") or "http://localhost:11434"

        if provider == "gemini":
            return cls.call_gemini(prompt, api_key, model)
        elif provider == "openai":
            return cls.call_openai_compatible(prompt, api_key, "https://api.openai.com/v1", model or "gpt-4o-mini")
        elif provider == "groq":
            return cls.call_openai_compatible(prompt, api_key, "https://api.groq.com/openai/v1", model or "llama-3.3-70b-versatile")
        elif provider == "anthropic":
            return cls.call_anthropic(prompt, api_key, model or "claude-3-5-haiku-20241022")
        elif provider == "ollama":
            return cls.call_ollama(prompt, ollama_url, model or "llama3.2")
        return None

    @classmethod
    def generate_pitches(
        cls,
        company: str,
        role: str,
        snippet: str,
        profile_data: Dict[str, Any],
        ai_config: Dict[str, Any],
        lead_type: str = "job",
        focus_angle: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate tailored Email, LinkedIn note, and Elevator pitch."""
        name = profile_data.get("full_name") or "Candidate"
        headline = profile_data.get("headline") or "Software Engineer"
        bio = profile_data.get("bio") or ""
        skills = ", ".join(profile_data.get("skills", [])[:8])
        clean_snippet = (snippet or "")[:600].replace("\n", " ").strip()

        # Offline fallback
        if lead_type == "client":
            fallback_email = (
                f"Hi {company} Team,\n\n"
                f"I noticed your project requirements for {role}. "
                f"As an independent {headline}, I specialize in building robust production software with {skills}.\n\n"
                f"I've worked extensively on similar challenges and can deliver high-velocity sprint execution for your stack. "
                f"Let's schedule a brief 10-minute sync to discuss your roadmap.\n\n"
                f"Best,\n{name}"
            )
            fallback_li = f"Hi {company} Team, saw your {role} requirements. As a {headline} ({skills}), I help teams ship rapid, high-impact solutions. Let's connect!"
            fallback_elevator = (
                f"I specialize as a {headline} with deep hands-on expertise in {skills}. "
                f"For {company}'s {role} project, I can immediately take ownership of core delivery milestones and accelerate implementation."
            )
        else:
            fallback_email = (
                f"Hi {company} Hiring Team,\n\n"
                f"I saw your opening for {role} and wanted to reach out directly. "
                f"As a {headline} with experience in {skills}, my background aligns closely with your technical objectives.\n\n"
                f"I take full ownership of end-to-end architecture and thrive in high-impact product engineering environments. "
                f"I would welcome the opportunity to connect and discuss how I can contribute to {company}.\n\n"
                f"Best regards,\n{name}"
            )
            fallback_li = f"Hi {company} Team, saw your {role} role! As a {headline} ({skills}), I build resilient production systems and would love to connect."
            fallback_elevator = (
                f"As a {headline} proficient in {skills}, I bridge technical architecture with rapid execution. "
                f"I am eager to bring my engineering discipline to {company}'s {role} position."
            )

        if len(fallback_li) > 295:
            fallback_li = fallback_li[:292] + "..."

        fallback_res = {
            "email": fallback_email,
            "linkedin": fallback_li,
            "elevator_pitch": fallback_elevator
        }

        angle_prompt = f"Focus on this specific angle: {focus_angle}." if focus_angle else ""

        prompt = f"""You are writing high-conversion multi-channel job outreach assets for a candidate.

Candidate Profile:
- Full Name: {name}
- Headline: {headline}
- Key Skills: {skills}
- Background: {bio}

Opportunity Details:
- Company: {company}
- Target Role: {role}
- Job Description Snippet: {clean_snippet}
- Lead Type: {lead_type} (either full-time 'job' or contract/freelance 'client')
{angle_prompt}

Generate 3 high-impact assets:
1. "email": A 3-paragraph personalized pitch connecting candidate's exact strengths to {company}'s needs. Sign off with {name}.
2. "linkedin": A punchy LinkedIn connection note strictly UNDER 280 CHARACTERS (character count limit is critical).
3. "elevator_pitch": A 2-paragraph conversational elevator pitch / cover snippet explaining why {name} is the ideal fit.

Return ONLY a valid JSON object matching this schema:
{{
  "email": "...",
  "linkedin": "...",
  "elevator_pitch": "..."
}}"""

        raw_response = cls.generate_text(prompt, ai_config)
        if raw_response:
            try:
                json_match = re.search(r"(\{.*\})", raw_response, re.DOTALL)
                raw_json = json_match.group(1) if json_match else raw_response.strip()
                clean_json = re.sub(r"^```json\s*", "", raw_json.strip())
                clean_json = re.sub(r"\s*```$", "", clean_json.strip())
                parsed = json.loads(clean_json)
                if isinstance(parsed, dict) and "email" in parsed and "linkedin" in parsed:
                    li = parsed.get("linkedin", "")
                    if len(li) > 295:
                        parsed["linkedin"] = li[:292] + "..."
                    return {
                        "email": parsed.get("email", fallback_email),
                        "linkedin": parsed.get("linkedin", fallback_li),
                        "elevator_pitch": parsed.get("elevator_pitch", fallback_elevator)
                    }
            except Exception:
                pass

        return fallback_res
