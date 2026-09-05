from datetime import datetime, timezone

from flask import Blueprint, redirect, render_template, request, session, url_for

from ai.career_ai import coach_response
from app import get_db

career_bp = Blueprint("career", __name__)


@career_bp.route("/career", methods=["GET", "POST"])
def career():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    advice = None
    if request.method == "POST":
        goal = request.form.get("goal", "").strip()
        background = request.form.get("background", "").strip()
        level = request.form.get("level", "Mid-Level (2-5 yrs)")
        timeline = request.form.get("timeline", "90 Days")

        if goal:
            advice = coach_response(goal, background, level, timeline)
            db = get_db()
            db.execute(
                "INSERT INTO activity (user_id, kind, title, score, created_at) VALUES (?, ?, ?, ?, ?)",
                (session["user_id"], "career", f"Career roadmap: {goal[:30]}", advice["readiness_score"], datetime.now(timezone.utc).isoformat())
            )
            db.commit()

    return render_template(
        "career_coach.html",
        advice=advice,
        goal=request.form.get("goal", ""),
        background=request.form.get("background", ""),
        selected_level=request.form.get("level", "Mid-Level (2-5 yrs)"),
        selected_timeline=request.form.get("timeline", "90 Days")
    )
