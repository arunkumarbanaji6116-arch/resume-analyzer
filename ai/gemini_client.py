import json
import logging
import re

from config import Config

logger = logging.getLogger(__name__)

_client = None


def get_gemini_client():
    global _client
    if _client is not None:
        return _client
    api_key = Config.GEMINI_API_KEY
    if not api_key or api_key == "change-this-before-production":
        return None
    try:
        from google import genai
        _client = genai.Client(api_key=api_key)
        return _client
    except Exception as e:
        logger.warning(f"Could not initialize Gemini Client: {e}")
        return None


CANDIDATE_MODELS = ["gemini-flash-lite-latest", "gemini-3.1-flash-lite-preview", "gemini-flash-latest"]


def _call_gemini_json(prompt: str) -> dict | None:
    client = get_gemini_client()
    if not client:
        return None

    from google.genai import types

    for model in CANDIDATE_MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            if response and response.text:
                return json.loads(response.text)
        except Exception as e:
            logger.warning(f"Gemini call with {model} failed: {e}")
            continue

    return None


def gemini_analyze_job(description: str, resume: str) -> dict | None:
    prompt = f"""
You are an expert ATS and technical hiring manager. Analyze the match between this Job Description and Candidate Resume.

Job Description:
{description[:3500]}

Candidate Resume:
{resume[:3500]}

Respond ONLY with valid JSON matching this exact structure:
{{
  "match_score": <integer from 0 to 100 representing overall suitability and keyword fit>,
  "fit_level": "<one of: 'Strong Match', 'Competitive Match', 'Growth Opportunity / Stretch Role'>",
  "fit_color": "<'#087f5b' for Strong, '#6d5dfc' for Competitive, '#f76707' for Growth>",
  "summary": "<2-3 sentence executive assessment of the candidate's alignment with this position>",
  "matched": ["<list of 4-10 key technical and domain skills found in both>"],
  "missing": ["<list of 3-8 required or preferred skills/keywords missing from the resume>"],
  "recommendations": ["<3-4 concrete, actionable resume tailoring recommendations for this exact job>"]
}}
"""
    data = _call_gemini_json(prompt)
    if data and "match_score" in data:
        data["matched_count"] = len(data.get("matched", []))
        data["required_count"] = data["matched_count"] + len(data.get("missing", []))
        return data
    return None


def gemini_analyze_resume(text: str, target_role: str = "") -> dict | None:
    role_clause = f"Target Role: {target_role}\n" if target_role else ""
    prompt = f"""
You are a senior executive resume reviewer and hiring manager. Review this candidate's resume content.
{role_clause}
Resume Content:
{text[:4500]}

Respond ONLY with valid JSON matching this exact structure:
{{
  "score": <integer from 40 to 98 representing resume strength, impact, and ATS readiness>,
  "notes": [
    "<3 to 6 high-impact, specific, actionable feedback notes on content, action verbs, quantified metrics, and positioning>"
  ]
}}
"""
    data = _call_gemini_json(prompt)
    if data and "score" in data and "notes" in data:
        words = re.findall(r"\b[\w+#.-]+\b", text.lower())
        metrics = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", text))
        data["word_count"] = len(words)
        data["metrics"] = metrics
        return data
    return None


def gemini_coach_response(goal: str, background: str, level: str, timeline: str) -> dict | None:
    prompt = f"""
You are an executive career strategist and mentor. Create a high-value, structured career roadmap for this professional.

Target Goal: {goal}
Current Background: {background}
Current Career Level: {level}
Target Timeline: {timeline}

Respond ONLY with valid JSON matching this exact structure:
{{
  "summary": "<A powerful headline for this roadmap>",
  "readiness_score": <integer from 45 to 95 assessing current readiness for the target goal>,
  "phases": [
    {{
      "number": 1,
      "title": "<Phase 1 Title>",
      "timeframe": "<e.g. Weeks 1–3>",
      "focus": "<core phase objective>",
      "tasks": ["<task 1>", "<task 2>", "<task 3>"]
    }},
    {{
      "number": 2,
      "title": "<Phase 2 Title>",
      "timeframe": "<e.g. Weeks 4–7>",
      "focus": "<core phase objective>",
      "tasks": ["<task 1>", "<task 2>", "<task 3>"]
    }},
    {{
      "number": 3,
      "title": "<Phase 3 Title>",
      "timeframe": "<e.g. Weeks 8–9>",
      "focus": "<core phase objective>",
      "tasks": ["<task 1>", "<task 2>", "<task 3>"]
    }},
    {{
      "number": 4,
      "title": "<Phase 4 Title>",
      "timeframe": "<e.g. Weeks 10–12+>",
      "focus": "<core phase objective>",
      "tasks": ["<task 1>", "<task 2>", "<task 3>"]
    }}
  ],
  "sprints": [
    {{"week": "Sprint 1 (Week 1)", "task": "<specific actionable deliverable>"}},
    {{"week": "Sprint 2 (Week 2)", "task": "<specific actionable deliverable>"}},
    {{"week": "Sprint 3 (Week 3-4)", "task": "<specific actionable deliverable>"}},
    {{"week": "Sprint 4 (Week 5-6)", "task": "<specific actionable deliverable>"}},
    {{"week": "Sprint 5 (Week 7-8)", "task": "<specific actionable deliverable>"}},
    {{"week": "Sprint 6 (Week 9+)", "task": "<specific actionable deliverable>"}}
  ],
  "certifications": ["<top 3 recognized credentials for this role>"],
  "outreach_template": "<A personalized, high-converting LinkedIn networking message template for connecting with insiders in this target role>",
  "top_pitfall": "<The #1 mistake candidates make when targeting this role>",
  "unfair_advantage": "<The highest-leverage competitive edge this candidate should leverage>"
}}
"""
    data = _call_gemini_json(prompt)
    if data and "phases" in data and "readiness_score" in data:
        data["goal"] = goal
        data["level"] = level
        data["timeline"] = timeline
        return data
    return None


def gemini_assess_interview(answer: str, question: str) -> dict | None:
    prompt = f"""
You are an expert interviewer and interview coach. Assess this candidate's interview response using the STAR method (Situation, Task, Action, Result).

Interview Question:
{question}

Candidate's Answer:
{answer}

Respond ONLY with valid JSON matching this exact structure:
{{
  "score": <integer from 25 to 98 based on structure, depth, ownership, and measurable results>,
  "star": {{
    "situation": <true or false depending on whether context/situation was described>,
    "task": <true or false depending on whether personal responsibility/task was clarified>,
    "action": <true or false depending on whether concrete action verbs/steps were detailed>,
    "result": <true or false depending on whether measurable outcome/metrics/takeaway was shared>
  }},
  "strengths": ["<1 to 3 specific strengths of the response>"],
  "improvements": ["<1 to 3 actionable constructive feedback points to improve the answer>"],
  "feedback": "<2 sentence evaluator summary on delivery and impact>"
}}
"""
    data = _call_gemini_json(prompt)
    if data and "score" in data and "star" in data:
        words = re.findall(r"\b[\w+#.-]+\b", answer.lower())
        data["word_count"] = len(words)
        return data
    return None

