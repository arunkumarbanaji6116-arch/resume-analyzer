from datetime import datetime, timezone

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from ai.interview_ai import assess_answer, questions_for
from app import get_db

interview_bp = Blueprint("interview", __name__)


@interview_bp.route("/interview", methods=["GET", "POST"])
def setup():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        session["interview_role"] = request.form.get("role", "General")
        session["interview_count"] = int(request.form.get("question_count", 5))
        return redirect(url_for("interview.room"))
    return render_template("interview_setup.html")


@interview_bp.get("/interview/room")
def room():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    role = session.get("interview_role", "General")
    count = session.get("interview_count", 5)
    all_questions = questions_for(role)
    selected_questions = all_questions[:count]
    return render_template(
        "interview_room.html",
        role=role,
        questions=selected_questions,
        total_count=len(selected_questions)
    )


@interview_bp.post("/interview/assess")
def assess():
    if "user_id" not in session:
        return jsonify({"error": "Please sign in."}), 401
    payload = request.get_json(silent=True) or {}
    answer = payload.get("answer", "")
    question = payload.get("question", "")
    result = assess_answer(answer, question)
    return jsonify(result)


@interview_bp.post("/interview/complete")
def complete():
    if "user_id" not in session:
        return jsonify({"error": "Please sign in."}), 401
    payload = request.get_json(silent=True) or {}
    overall_score = payload.get("overall_score", 0)
    role = session.get("interview_role", "General")
    count = payload.get("question_count", session.get("interview_count", 5))

    db = get_db()
    db.execute(
        "INSERT INTO activity (user_id, kind, title, score, created_at) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], "interview", f"Mock interview ({count} questions): {role}", overall_score, datetime.now(timezone.utc).isoformat())
    )
    db.commit()
    return jsonify({"success": True, "score": overall_score})
