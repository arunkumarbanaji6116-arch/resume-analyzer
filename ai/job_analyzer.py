import re

TECH_SKILLS = {
    "python", "javascript", "typescript", "java", "c++", "c#", "golang", "go", "rust", "ruby", "php", "swift", "kotlin", "sql",
    "react", "next.js", "vue", "angular", "node.js", "node", "express", "django", "flask", "fastapi", "spring boot", "spring", ".net",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd", "git", "linux", "kafka", "redis", "postgresql", "mongodb", "mysql",
    "machine learning", "deep learning", "pytorch", "tensorflow", "pandas", "numpy", "spark", "tableau", "power bi", "excel", "etl", "rest api", "graphql", "microservices"
}

SOFT_SKILLS = {
    "leadership", "communication", "project management", "collaboration", "problem solving",
    "agile", "scrum", "stakeholder management", "mentoring", "critical thinking", "ownership", "adaptability"
}

ALL_SKILLS = TECH_SKILLS | SOFT_SKILLS


def extract_skills(text: str) -> set:
    text_lower = text.lower()
    found = set()
    for skill in ALL_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill)
    return found


def analyze_job(description: str, resume: str = "") -> dict:
    try:
        from ai.gemini_client import gemini_analyze_job
        gemini_result = gemini_analyze_job(description, resume)
        if gemini_result:
            return gemini_result
    except Exception as e:
        pass

    req_skills = extract_skills(description)
    resume_skills = extract_skills(resume)

    matched = sorted(list(req_skills & resume_skills))
    missing = sorted(list(req_skills - resume_skills))

    matched_tech = [s for s in matched if s in TECH_SKILLS]
    matched_soft = [s for s in matched if s in SOFT_SKILLS]
    missing_tech = [s for s in missing if s in TECH_SKILLS]
    missing_soft = [s for s in missing if s in SOFT_SKILLS]

    if req_skills:
        score = min(100, round((len(matched) / len(req_skills)) * 100))
    else:
        # Fallback keyword overlap if no curated skills found
        desc_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", description.lower()))
        res_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", resume.lower()))
        overlap = desc_words & res_words
        score = min(100, round((len(overlap) / max(len(desc_words), 1)) * 100)) if desc_words else 50
        matched = sorted(list(overlap))[:10]
        missing = sorted(list(desc_words - res_words))[:8]
        matched_tech = matched
        matched_soft = []
        missing_tech = missing
        missing_soft = []

    if score >= 75:
        fit_level = "Strong Match"
        fit_color = "#087f5b"
        summary = "You meet most key requirements for this position! Focus on highlighting your quantified achievements."
    elif score >= 50:
        fit_level = "Competitive Match"
        fit_color = "#6d5dfc"
        summary = "You have solid foundational overlap. Address the missing skills in your summary or project bullets."
    else:
        fit_level = "Growth Opportunity / Stretch Role"
        fit_color = "#f76707"
        summary = "Consider bridging key skill gaps through hands-on portfolio projects or related transferrable experience."

    recommendations = []
    if missing_tech:
        recommendations.append(f"Incorporate technical keywords you know: {', '.join(missing_tech[:4])}.")
    if missing_soft:
        recommendations.append(f"Demonstrate leadership & process skills: {', '.join(missing_soft[:3])}.")
    if len(resume.split()) < 150:
        recommendations.append("Expand on your projects and concrete responsibilities to improve ATS match fidelity.")
    if not recommendations:
        recommendations.append("Tailor your bullet points using the exact phrasing from this job description.")

    return {
        "match_score": score,
        "fit_level": fit_level,
        "fit_color": fit_color,
        "summary": summary,
        "matched": matched,
        "missing": missing,
        "matched_tech": matched_tech,
        "matched_soft": matched_soft,
        "missing_tech": missing_tech,
        "missing_soft": missing_soft,
        "required_count": len(req_skills),
        "matched_count": len(matched),
        "recommendations": recommendations,
    }
