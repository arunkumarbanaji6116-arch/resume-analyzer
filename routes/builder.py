from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ai.gemini_client import gemini_build_resume_from_scratch
from db import get_db, record_activity

builder_bp = Blueprint("builder", __name__)


@builder_bp.get("/builder")
def builder_view():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    prefill = {
        "name": session.get("user", ""),
        "target_role": request.args.get("role", ""),
        "experience_level": request.args.get("level", "Mid-Level"),
        "skills": request.args.get("skills", ""),
    }
    return render_template("builder.html", prefill=prefill, resume=None)


@builder_bp.post("/builder/generate")
def generate_resume():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    data = {
        "name": request.form.get("name", "").strip() or session.get("user", "Candidate"),
        "email": request.form.get("email", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "location": request.form.get("location", "").strip(),
        "linkedin": request.form.get("linkedin", "").strip(),
        "target_role": request.form.get("target_role", "").strip() or "Software Engineer",
        "experience_level": request.form.get("experience_level", "Mid-Senior"),
        "industry": request.form.get("industry", "Technology"),
        "skills": request.form.get("skills", "").strip(),
        "experience_raw": request.form.get("experience_raw", "").strip(),
        "education_raw": request.form.get("education_raw", "").strip(),
        "projects_raw": request.form.get("projects_raw", "").strip(),
    }

    strategy = request.form.get("strategy", "metric_driven")
    try:
        variation_seed = int(request.form.get("variation_seed", 1))
    except (ValueError, TypeError):
        variation_seed = 1

    generated = gemini_build_resume_from_scratch(data, strategy=strategy, variation_seed=variation_seed)

    record_activity(
        session["user_id"],
        "resume_builder",
        f"Resume Builder: {data['target_role']} (Gen #{variation_seed} · {generated.get('strategy_title', strategy)})",
        generated.get("ats_score", 97),
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return {"status": "ok", "resume": generated}

    return render_template("builder.html", prefill=data, resume=generated, active_strategy=strategy, current_seed=variation_seed)

