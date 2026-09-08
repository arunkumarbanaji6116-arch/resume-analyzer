from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ai.resume_ai import ResumeImageError, analyze_resume, extract_text_from_resume_image
from db import get_db

resume_bp = Blueprint("resume", __name__)


@resume_bp.route("/resume", methods=["GET", "POST"])
def resume():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    analysis = None
    if request.method == "POST":
        role = request.form.get("target_role", "").strip()
        resume_image = request.files.get("resume_image")

        if not resume_image or not resume_image.filename:
            flash("Please upload your resume (PDF, DOCX, PNG, JPG, or WEBP) to begin the review.")
        else:
            extension = resume_image.filename.rsplit(".", 1)[-1].lower() if "." in resume_image.filename else ""
            allowed_extensions = {"pdf", "docx", "doc", "txt", "rtf", "png", "jpg", "jpeg", "webp"}
            if extension and extension not in allowed_extensions:
                flash("Unsupported format. Please upload a PDF, DOCX, DOC, TXT, or image file.")
            else:
                try:
                    text = extract_text_from_resume_image(resume_image)
                    analysis = analyze_resume(text, role)
                    analysis["source"] = f"uploaded file ({resume_image.filename})"
                    analysis["raw_text"] = text
                    analysis["target_role"] = role
                    db = get_db()
                    db.execute(
                        "INSERT INTO activity (user_id, kind, title, score, created_at) VALUES (?, ?, ?, ?, ?)",
                        (session["user_id"], "resume", f"Resume review: {role or 'General'}", analysis["score"], datetime.now(timezone.utc).isoformat())
                    )
                    db.commit()
                except ResumeImageError as error:
                    flash(str(error))
    return render_template("resume.html", analysis=analysis)


@resume_bp.post("/resume/improve")
def improve():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    text = request.form.get("resume_text", "").strip()
    role = request.form.get("target_role", "").strip()
    try:
        initial_score = int(request.form.get("initial_score", 70))
    except (ValueError, TypeError):
        initial_score = 70
    notes = request.form.getlist("notes")
    try:
        variation_index = int(request.form.get("variation_index", 1))
    except (ValueError, TypeError):
        variation_index = 1

    from ai.gemini_client import gemini_improve_resume
    improved_data = gemini_improve_resume(text, role, initial_score, notes, variation_index)

    db = get_db()
    db.execute(
        "INSERT INTO activity (user_id, kind, title, score, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            session["user_id"],
            "resume_boost",
            f"Resume Boost: {role or 'General'} (+{improved_data.get('score_boost', 25)} pts)",
            improved_data["improved_score"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    db.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return {"status": "ok", "improved": improved_data}

    synthetic_analysis = {
        "score": initial_score,
        "raw_text": text,
        "target_role": role,
        "notes": notes,
        "source": "Uploaded resume",
        "word_count": len(text.split()),
        "metrics": 2,
    }
    return render_template("resume.html", analysis=synthetic_analysis, improved=improved_data)

