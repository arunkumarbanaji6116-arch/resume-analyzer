import re

CERTIFICATIONS_BY_FIELD = {
    "cloud": ["AWS Certified Solutions Architect (Associate)", "Google Cloud Professional Cloud Architect", "Azure Administrator (AZ-104)"],
    "data": ["Google Data Analytics Professional Certificate", "AWS Certified Data Analytics", "Databricks Certified Data Engineer"],
    "software": ["Meta Full-Stack Developer Certificate", "CKA (Certified Kubernetes Administrator)", "Docker Certified Associate"],
    "product": ["Product School Certified Product Manager (CPM)", "Pragmatic Institute Certified (PMC)", "Scrum Alliance Certified Scrum Product Owner (CSPO)"],
    "security": ["CompTIA Security+", "CISSP (Certified Information Systems Security Professional)", "AWS Certified Security Specialty"],
    "general": ["PMP (Project Management Professional)", "Certified ScrumMaster (CSM)", "Six Sigma Green Belt"]
}


def _detect_certifications(goal_lower: str, bg_lower: str) -> list:
    if any(w in goal_lower for w in ["cloud", "devops", "aws", "infrastructure", "sre"]):
        return CERTIFICATIONS_BY_FIELD["cloud"]
    if any(w in goal_lower for w in ["data", "analytics", "bi", "scientist", "analyst", "ml", "ai"]):
        return CERTIFICATIONS_BY_FIELD["data"]
    if any(w in goal_lower for w in ["product", "pm", "owner", "program"]):
        return CERTIFICATIONS_BY_FIELD["product"]
    if any(w in goal_lower for w in ["security", "cyber", "infosec"]):
        return CERTIFICATIONS_BY_FIELD["security"]
    if any(w in goal_lower for w in ["software", "developer", "engineer", "frontend", "backend", "fullstack"]):
        return CERTIFICATIONS_BY_FIELD["software"]
    return CERTIFICATIONS_BY_FIELD["general"]


def coach_response(goal: str, background: str, level: str = "Mid-Level (2-5 yrs)", timeline: str = "90 Days") -> dict:
    try:
        from ai.gemini_client import gemini_coach_response
        gemini_result = gemini_coach_response(goal, background, level, timeline)
        if gemini_result:
            return gemini_result
    except Exception:
        pass

    goal_clean = goal.strip() or "your next target role"
    bg_clean = background.strip()
    goal_lower = goal_clean.lower()
    bg_lower = bg_clean.lower()

    # Calculate baseline readiness score
    bg_words = len(re.findall(r"\b\w+\b", bg_lower))
    has_metrics = bool(re.search(r"\b\d+[%+]?\b", bg_clean))
    has_skills = any(w in bg_lower for w in ["python", "sql", "lead", "manage", "deliver", "build", "design", "agile", "experience", "degree"])
    
    base_score = 45
    if bg_words > 40:
        base_score += 15
    if has_metrics:
        base_score += 15
    if has_skills:
        base_score += 15
    if "senior" in level.lower() or "lead" in level.lower():
        base_score = min(92, base_score + 5)
    readiness_score = min(94, max(42, base_score))

    # Phase 1: Skills & Competency
    phase1_tasks = [
        f"Audit 10 top job descriptions for {goal_clean} and document the top 5 non-negotiable tools.",
        "Dedicate 60–90 minutes daily to hands-on skill bridging using documentation and interactive labs.",
        "Complete a baseline skill diagnostic test to identify your highest-leverage improvement area."
    ]

    # Phase 2: Proof of Work & Portfolio
    phase2_tasks = [
        f"Build a flagship case study/project specifically solving a realistic problem in {goal_clean}.",
        "Include measurable impact metrics, clear architecture or process diagrams, and a live demo/writeup.",
        "Publish your project walkthrough to GitHub or a personal portfolio page with an executive summary."
    ]

    # Phase 3: Narrative & Resume Optimization
    phase3_tasks = [
        f"Rewrite your resume headline and top summary directly mirroring the terminology of {goal_clean}.",
        "Reframe past experience into Action + Context + Quantified Outcome bullet points.",
        "Optimize your LinkedIn profile headline, About section, and featured portfolio links for recruiter search filters."
    ]

    # Phase 4: Strategic Outreach & Interview Execution
    phase4_tasks = [
        "Conduct 3 informational interviews weekly with practitioners already working in your target role.",
        "Request internal referrals before submitting direct applications to skip the automated ATS queue.",
        "Run mock behavioral and domain drills using the STAR framework to build conviction and brevity."
    ]

    phases = [
        {
            "number": 1,
            "title": "Foundation & Targeted Skill Building",
            "timeframe": "Weeks 1–3",
            "focus": "Close critical skill gaps and master high-demand domain tooling.",
            "tasks": phase1_tasks
        },
        {
            "number": 2,
            "title": "Proof of Work & Project Execution",
            "timeframe": "Weeks 4–7",
            "focus": "Produce undeniable, publicly demonstrable proof of your capabilities.",
            "tasks": phase2_tasks
        },
        {
            "number": 3,
            "title": "Narrative Alignment & Positioning",
            "timeframe": "Weeks 8–9",
            "focus": "Reposition your resume, portfolio, and LinkedIn presence to match market standards.",
            "tasks": phase3_tasks
        },
        {
            "number": 4,
            "title": "High-Impact Outreach & Interview Mastery",
            "timeframe": "Weeks 10–12+",
            "focus": "Secure warm referrals and convert interview rounds into concrete offers.",
            "tasks": phase4_tasks
        }
    ]

    sprints = [
        {"week": "Sprint 1 (Week 1)", "task": f"Deconstruct 10 job postings for {goal_clean}; shortlist 3 core skills to elevate."},
        {"week": "Sprint 2 (Week 2)", "task": "Set up learning environment and start building a dedicated portfolio project."},
        {"week": "Sprint 3 (Week 3-4)", "task": "Complete initial project milestone; write clear technical documentation."},
        {"week": "Sprint 4 (Week 5-6)", "task": "Redesign resume with quantified achievements; align LinkedIn headline."},
        {"week": "Sprint 5 (Week 7-8)", "task": "Reach out to 5 alumni or professionals in your target company for advice."},
        {"week": "Sprint 6 (Week 9+)", "task": "Begin structured mock interview sessions and submit referral-backed applications."}
    ]

    certifications = _detect_certifications(goal_lower, bg_lower)

    outreach_template = (
        f"Hi [Name], I noticed your impressive journey in {goal_clean} at [Company]. "
        f"I'm currently preparing for a role in this space with a background in {bg_clean[:60] or 'industry'}. "
        "I'd love to ask 2 quick questions about how your team approaches challenges. "
        "Would you be open to a 10-minute coffee chat or async message? Either way, keep up the great work!"
    )

    return {
        "goal": goal_clean,
        "summary": f"Your Strategic Roadmap to {goal_clean}",
        "readiness_score": readiness_score,
        "level": level,
        "timeline": timeline,
        "phases": phases,
        "sprints": sprints,
        "certifications": certifications,
        "outreach_template": outreach_template,
        "top_pitfall": "Applying blindly through cold job boards without a tailored narrative or warm referral.",
        "unfair_advantage": "Candidates who showcase 1 deep, polished case study with real business metrics consistently outperform applicants with 10 generic bullet points."
    }
