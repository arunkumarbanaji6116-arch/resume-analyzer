from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ai.job_analyzer import analyze_job
from ai.resume_ai import ResumeImageError, extract_text_from_resume_image
from app import get_db

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/jobs", methods=["GET", "POST"])
def jobs():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    analysis = None
    if request.method == "POST":
        job_description = request.form.get("job_description", "").strip()
        resume_text = request.form.get("resume_text", "").strip()

        job_image = request.files.get("job_image")
        resume_image = request.files.get("resume_image")

        # Process Job Description image via OCR if uploaded
        if job_image and job_image.filename:
            try:
                extracted_job_text = extract_text_from_resume_image(job_image)
                job_description = "\n".join(filter(None, (job_description, extracted_job_text)))
            except ResumeImageError as err:
                flash(f"Job image error: {err}")

        # Process Resume image via OCR if uploaded
        if resume_image and resume_image.filename:
            try:
                extracted_resume_text = extract_text_from_resume_image(resume_image)
                resume_text = "\n".join(filter(None, (resume_text, extracted_resume_text)))
            except ResumeImageError as err:
                flash(f"Resume image error: {err}")

        if not job_description:
            flash("Please provide a job description by pasting text or uploading a job posting screenshot.")
        elif not resume_text:
            flash("Please provide your resume by pasting text or uploading a resume image.")
        else:
            analysis = analyze_job(job_description, resume_text)
            db = get_db()
            db.execute(
                "INSERT INTO activity (user_id, kind, title, score, created_at) VALUES (?, ?, ?, ?, ?)",
                (session["user_id"], "job", "Job match analysis", analysis["match_score"], datetime.now(timezone.utc).isoformat())
            )
            db.commit()

    return render_template(
        "job_analyzer.html",
        analysis=analysis,
        job_description=request.form.get("job_description", ""),
        resume_text=request.form.get("resume_text", "")
    )
