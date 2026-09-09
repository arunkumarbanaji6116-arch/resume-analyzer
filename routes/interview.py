from datetime import datetime, timezone

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from config import Config
from ai.interview_ai import assess_answer, questions_for, mcq_questions_for
from ai.voice_ai import generate_speech, VOICES
from db import get_db, record_activity
from flask import Response

interview_bp = Blueprint("interview", __name__)


@interview_bp.route("/interview", methods=["GET", "POST"])
def setup():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        session["interview_role"] = request.form.get("role", "General")
        session["interview_type"] = request.form.get("interview_type", "star")
        session["interview_count"] = int(request.form.get("question_count", 5))
        session["interview_voice"] = request.form.get("voice", "rachel")
        session["interview_auto_speak"] = request.form.get("auto_speak") != "off"
        return redirect(url_for("interview.room"))
    return render_template(
        "interview_setup.html",
        elevenlabs_configured=bool(Config.ELEVENLABS_API_KEY),
        voices=VOICES
    )


@interview_bp.get("/interview/room")
def room():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    role = session.get("interview_role", "General")
    interview_type = session.get("interview_type", "star")
    count = session.get("interview_count", 5)
    voice = session.get("interview_voice", "rachel")
    auto_speak = session.get("interview_auto_speak", True)
    
    if interview_type == "mcq":
        all_questions = mcq_questions_for(role)
    else:
        all_questions = questions_for(role)

    selected_questions = all_questions[:count]
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
def speak():
    if "user_id" not in session:
        return jsonify({"error": "Please sign in."}), 401
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "").strip()
    voice = payload.get("voice") or session.get("interview_voice", "rachel")

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
def assess():
    if "user_id" not in session:
        return jsonify({"error": "Please sign in."}), 401
    payload = request.get_json(silent=True) or {}
    interview_type = payload.get("interview_type") or session.get("interview_type", "star")
    
    if interview_type == "mcq":
        selected = payload.get("selected_option", "")
        correct = payload.get("correct_option", "")
        explanation = payload.get("explanation", "")
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

    record_activity(
        session["user_id"],
        "interview",
        f"Mock interview ({count} questions): {role}",
        overall_score,
    )
    return jsonify({"success": True, "score": overall_score})
