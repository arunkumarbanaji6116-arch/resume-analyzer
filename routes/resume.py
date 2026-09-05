from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ai.resume_ai import ResumeImageError, analyze_resume, extract_text_from_resume_image
from app import get_db

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
            flash("Please upload a resume image (PNG, JPG, JPEG, or WEBP) to begin the review.")
        else:
            extension = resume_image.filename.rsplit(".", 1)[-1].lower() if "." in resume_image.filename else ""
            if extension not in {"jpg", "jpeg", "png", "webp"}:
                flash("Unsupported format. Please upload a PNG, JPG, JPEG, or WEBP image.")
            else:
                try:
                    text = extract_text_from_resume_image(resume_image)
                    analysis = analyze_resume(text, role)
                    analysis["source"] = f"uploaded image ({resume_image.filename})"
                    db = get_db()
                    db.execute(
                        "INSERT INTO activity (user_id, kind, title, score, created_at) VALUES (?, ?, ?, ?, ?)",
                        (session["user_id"], "resume", f"Resume review: {role or 'General'}", analysis["score"], datetime.now(timezone.utc).isoformat())
                    )
                    db.commit()
                except ResumeImageError as error:
                    flash(str(error))
    return render_template("resume.html", analysis=analysis)
