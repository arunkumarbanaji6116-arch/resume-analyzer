import re

QUESTIONS = {
    "Software Engineer": [
        {"category": "Technical Architecture", "text": "Tell me about a complex feature or system you designed and built end to end. What tradeoffs did you make?"},
        {"category": "Problem Solving", "text": "Describe a time when you had to debug an elusive, high-priority production bug. How did you isolate root cause?"},
        {"category": "Collaboration & Conflict", "text": "Tell me about a situation where you had a major technical disagreement with a teammate or lead. How did you resolve it?"},
        {"category": "System Scaling", "text": "How do you approach optimizing database queries and backend latency when traffic surges?"},
        {"category": "Ownership & Impact", "text": "Describe a project that did not go as planned or missed a deadline. What did you learn and how did you adjust?"}
    ],
    "Frontend Developer": [
        {"category": "Architecture & State", "text": "How do you decide between local component state, global state management, and server state caching in a large React/Next.js app?"},
        {"category": "Web Performance", "text": "Walk me through how you optimize Core Web Vitals (LCP, FID/INP, CLS) on a heavy web application."},
        {"category": "Component Design", "text": "Tell me about an accessible, reusable design system component you built from scratch. How did you ensure testability?"},
        {"category": "Cross-Functional", "text": "Describe a time a designer gave you an impractical or ambiguous UI specification. How did you collaborate to reach a solution?"},
        {"category": "Behavioral", "text": "Tell me about a time you had to deliver a critical frontend release under tight deadline pressure."}
    ],
    "Backend Developer": [
        {"category": "API & Data Modeling", "text": "Walk me through your thought process when designing a high-throughput REST or GraphQL API from scratch."},
        {"category": "Concurrency & Resilience", "text": "How do you prevent race conditions, implement distributed locks, and handle eventual consistency?"},
        {"category": "Database Tuning", "text": "Describe a time you diagnosed and resolved a severe database bottleneck or locking issue in production."},
        {"category": "System Tradeoffs", "text": "When would you choose an asynchronous message queue (e.g. Kafka, RabbitMQ) over synchronous HTTP communication?"},
        {"category": "Failure Recovery", "text": "Tell me about a production outage you responded to. What was the blast radius and what postmortem actions did you take?"}
    ],
    "Data Analyst": [
        {"category": "Business Impact", "text": "Walk me through an analytical finding you uncovered that directly changed a business or product decision."},
        {"category": "Data Quality", "text": "How do you validate messy or incomplete data before presenting insights to executive leadership?"},
        {"category": "Data Storytelling", "text": "Explain a complex statistical or predictive modeling result to an entirely non-technical stakeholder."},
        {"category": "Prioritization", "text": "Describe a time multiple teams requested urgent dashboard reports simultaneously. How did you prioritize?"},
        {"category": "Behavioral", "text": "Tell me about a time your data analysis contradicted the prevailing opinion of senior management. What did you do?"}
    ],
    "Product Manager": [
        {"category": "Product Strategy", "text": "How do you prioritize your product roadmap when balancing customer feature requests, tech debt, and strategic bets?"},
        {"category": "Metric Diagnostics", "text": "If a core engagement metric dropped by 18% week-over-week, walk me through your step-by-step diagnostic plan."},
        {"category": "Stakeholder Influence", "text": "Tell me about a time you had to say 'no' to an influential stakeholder or executive. How did you communicate the decision?"},
        {"category": "Launch & Iteration", "text": "Describe a product or feature launch that underperformed initial goals. How did you iterate post-launch?"},
        {"category": "Customer Discovery", "text": "How do you conduct customer discovery interviews to validate an unproven problem before committing engineering resources?"}
    ],
    "DevOps / Cloud Engineer": [
        {"category": "CI/CD & Automation", "text": "How do you design a zero-downtime deployment pipeline with automated canary testing and rollback mechanisms?"},
        {"category": "Incident Management", "text": "Describe how you diagnosed and resolved a major cloud infrastructure outage or network partition."},
        {"category": "Infrastructure as Code", "text": "How do you manage state and avoid drift in a multi-environment Terraform or Kubernetes setup?"},
        {"category": "Security & Compliance", "text": "Walk me through how you secure container images, manage secrets, and enforce least-privilege IAM policies."},
        {"category": "Cost Optimization", "text": "Tell me about an initiative where you analyzed and significantly reduced cloud infrastructure spend without degrading SLA."}
    ],
    "General": [
        {"category": "Career Motivation", "text": "Walk me through your background and the pivotal career decisions that led you to this role."},
        {"category": "Problem Solving", "text": "Describe the most challenging obstacle you overcame in the last 12 months. What was the outcome?"},
        {"category": "Leadership & Ownership", "text": "Tell me about a time you noticed an organizational or technical problem that was not your responsibility, but you stepped up to solve it."},
        {"category": "Adaptability", "text": "Describe a situation where project priorities completely changed halfway through. How did you adapt?"},
        {"category": "Constructive Feedback", "text": "Tell me about the toughest piece of critical feedback you received and how you actively worked to address it."}
    ]
}


def questions_for(role: str) -> list:
    return QUESTIONS.get(role, QUESTIONS["General"])


STAR_KEYWORDS = {
    "situation": ["situation", "context", "background", "when", "company", "project", "client", "team", "working at", "faced"],
    "task": ["task", "goal", "target", "needed to", "responsible for", "objective", "challenge", "assigned", "requirement"],
    "action": ["built", "designed", "developed", "led", "created", "implemented", "refactored", "analyzed", "coordinated", "resolved", "spearheaded", "executed"],
    "result": ["result", "impact", "increased", "decreased", "reduced", "improved", "saved", "%", "percent", "metric", "revenue", "achieved", "learned", "outcome"]
}


def assess_answer(answer: str, question: str = "") -> dict:
    text = answer.strip()
    words = re.findall(r"\b[\w+#.-]+\b", text.lower())
    word_count = len(words)

    if word_count < 10:
        return {
            "score": 25,
            "star": {"situation": False, "task": False, "action": False, "result": False},
            "strengths": ["Answer was submitted."],
            "improvements": ["Your answer is too brief. Provide a structured response with context, actions, and quantifiable results."],
            "feedback": "Answer is too short. Use the STAR technique to explain the Situation, your Task, concrete Actions, and measurable Results."
        }

    try:
        from ai.gemini_client import gemini_assess_interview
        gemini_result = gemini_assess_interview(answer, question)
        if gemini_result:
            return gemini_result
    except Exception:
        pass

    text_lower = text.lower()
    has_situation = any(k in text_lower for k in STAR_KEYWORDS["situation"]) or word_count > 60
    has_task = any(k in text_lower for k in STAR_KEYWORDS["task"])
    has_action = any(k in text_lower for k in STAR_KEYWORDS["action"])
    has_result = any(k in text_lower for k in STAR_KEYWORDS["result"]) or bool(re.search(r"\b\d+[%+]?\b", text))

    star_count = sum([has_situation, has_task, has_action, has_result])

    # Base scoring algorithm
    score = 40
    # Length points (target: 80 - 220 words)
    if word_count >= 80:
        score += 20
    elif word_count >= 40:
        score += 10

    # STAR structure points
    score += star_count * 9

    # Quantified metrics bonus
    metrics = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", text))
    if metrics >= 2:
        score += 8
    elif metrics == 1:
        score += 4

    score = min(98, max(30, score))

    strengths = []
    improvements = []

    if has_action:
        strengths.append("Strong active verbs demonstrating personal ownership.")
    if has_result or metrics > 0:
        strengths.append("Included tangible business or technical results.")
    if word_count >= 75:
        strengths.append("Sufficient narrative depth and detail.")
    if not strengths:
        strengths.append("Good start addressing the prompt directly.")

    if not has_result:
        improvements.append("Quantify the final result (e.g. % performance boost, time saved, revenue generated).")
    if not has_task:
        improvements.append("Clarify your specific responsibility or task within the larger team.")
    if word_count < 65:
        improvements.append("Expand on the technical or procedural decisions you made during the project.")
    if word_count > 300:
        improvements.append("Keep your answer concise (aim for ~90-180 words) to avoid rambling.")

    if score >= 80:
        feedback = "Outstanding response. Clear STAR structure, concrete actions, and impactful outcome."
    elif score >= 65:
        feedback = "Solid answer. Strengthen with more specific metrics or sharper action verbs."
    else:
        feedback = "Needs more structure. Detail your exact actions and the final measurable outcome using the STAR format."

    return {
        "score": score,
        "word_count": word_count,
        "star": {
            "situation": has_situation,
            "task": has_task,
            "action": has_action,
            "result": has_result
        },
        "strengths": strengths,
        "improvements": improvements or ["Continue practicing for fluid, confident delivery."],
        "feedback": feedback
    }
