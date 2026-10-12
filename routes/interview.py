from datetime import datetime, timezone

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for, Response

from config import Config
from ai.interview_ai import assess_answer, questions_for, mcq_questions_for
from ai.voice_ai import generate_speech, VOICES
from db import get_db, record_activity
from services.limiter import limiter
from services.security import login_required, sanitize_text

interview_bp = Blueprint("interview", __name__)


@interview_bp.route("/interview", methods=["GET", "POST"])
@login_required
def setup():
    if request.method == "POST":
        session["interview_role"] = sanitize_text(request.form.get("role", "General"), max_length=100)
        session["interview_type"] = sanitize_text(request.form.get("interview_type", "star"), max_length=50)
        try:
            session["interview_count"] = min(max(int(request.form.get("question_count", 5)), 1), 20)
        except (ValueError, TypeError):
            session["interview_count"] = 5
        session["interview_voice"] = sanitize_text(request.form.get("voice", "arun"), max_length=50)
        session["interview_auto_speak"] = request.form.get("auto_speak") != "off"
        return redirect(url_for("interview.room"))
    return render_template(
        "interview_setup.html",
        elevenlabs_configured=bool(Config.ELEVENLABS_API_KEY),
        voices=VOICES
    )


@interview_bp.route("/interview/refresh", methods=["GET", "POST"])
@login_required
def refresh():
    return redirect(url_for("interview.room"))


@interview_bp.get("/interview/room")
@login_required
def room():
    role = session.get("interview_role", "General")
    interview_type = session.get("interview_type", "star")
    count = session.get("interview_count", 5)
    voice = session.get("interview_voice", "arun")
    auto_speak = session.get("interview_auto_speak", True)
    
    # History of already presented questions to prevent loops
    asked_history = session.get("interview_question_history", [])
    if not isinstance(asked_history, list):
        asked_history = []

    # First attempt: dynamic generation via Gemini AI
    selected_questions = None
    try:
        from ai.gemini_client import gemini_generate_interview_questions
        selected_questions = gemini_generate_interview_questions(
            role=role,
            interview_type=interview_type,
            count=count,
            seen_questions=asked_history
        )
    except Exception:
        selected_questions = None

    # Fallback to randomized non-repeating questions from expanded bank
    if not selected_questions or len(selected_questions) < count:
        if interview_type == "mcq":
            selected_questions = mcq_questions_for(role, count=count, seen_questions=asked_history)
        else:
            selected_questions = questions_for(role, count=count, seen_questions=asked_history)

    # Save to session history to prevent repeating on next open
    new_texts = [q["text"] for q in selected_questions if isinstance(q, dict) and q.get("text")]
    session["interview_question_history"] = (asked_history + new_texts)[-60:]

    return render_template(
        "interview_room.html",
        role=role,
        interview_type=interview_type,
        questions=selected_questions,
        total_count=len(selected_questions),
        voice=voice,
        auto_speak=auto_speak,
        elevenlabs_configured=bool(Config.ELEVENLABS_API_KEY),
        voices=VOICES
    )


@interview_bp.post("/interview/speak")
@login_required
@limiter.limit("30 per minute")
def speak():
    payload = request.get_json(silent=True) or {}
    text = sanitize_text(payload.get("text", "").strip(), max_length=2000)
    voice = sanitize_text(payload.get("voice") or session.get("interview_voice", "arun"), max_length=50)

    if not text:
        return jsonify({"error": "Text is required."}), 400

    audio_bytes = generate_speech(text, voice)
    if audio_bytes:
        return Response(audio_bytes, mimetype="audio/mpeg")

    return jsonify({
        "fallback": True,
        "message": "ElevenLabs audio not generated; using speech synthesis."
    })


@interview_bp.post("/interview/assess")
@login_required
@limiter.limit("30 per minute")
def assess():
    payload = request.get_json(silent=True) or {}
    interview_type = payload.get("interview_type") or session.get("interview_type", "star")
    
    if interview_type == "mcq":
        selected = sanitize_text(payload.get("selected_option", ""), max_length=50)
        correct = sanitize_text(payload.get("correct_option", ""), max_length=50)
        explanation = sanitize_text(payload.get("explanation", ""), max_length=1000)
        is_correct = selected.strip().upper() == correct.strip().upper()
        score = 100 if is_correct else 0
        return jsonify({
            "is_correct": is_correct,
            "score": score,
            "selected": selected,
            "correct": correct,
            "explanation": explanation,
            "feedback": "Outstanding! You chose the optimal engineering solution." if is_correct else f"Incorrect. The optimal answer was Option {correct}."
        })

    answer = sanitize_text(payload.get("answer", ""), max_length=10000)
    question = sanitize_text(payload.get("question", ""), max_length=1000)
    result = assess_answer(answer, question)
    return jsonify(result)


@interview_bp.post("/interview/complete")
@login_required
@limiter.limit("30 per minute")
def complete():
    payload = request.get_json(silent=True) or {}
    try:
        overall_score = min(max(int(payload.get("overall_score", 0)), 0), 100)
    except (ValueError, TypeError):
        overall_score = 0
    role = session.get("interview_role", "General")
    try:
        count = min(max(int(payload.get("question_count", session.get("interview_count", 5))), 1), 50)
    except (ValueError, TypeError):
        count = 5

    record_activity(
        session["user_id"],
        "interview",
        f"Mock interview ({count} questions): {role}",
        overall_score,
    )
    return jsonify({"success": True, "score": overall_score})

