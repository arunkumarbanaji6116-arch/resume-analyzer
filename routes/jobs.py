from datetime import datetime, timezone
import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ai.job_analyzer import analyze_job
from ai.resume_ai import ResumeImageError, extract_text_from_resume_image
from db import get_db, record_activity

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/jobs", methods=["GET", "POST"])
def jobs():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    analysis = None
    job_description = ""
    resume_text = ""
    if request.method == "POST":
        job_description = request.form.get("job_description", "").strip()
        resume_text = request.form.get("resume_text", "").strip()

        job_image = request.files.get("job_image")
        resume_image = request.files.get("resume_image")

        # Process Job Description file/image via extraction if uploaded
        if job_image and job_image.filename:
            try:
                extracted_job_text = extract_text_from_resume_image(job_image)
                job_description = "\n".join(filter(None, (job_description, extracted_job_text)))
            except ResumeImageError as err:
                flash(f"Job posting error: {err}")

        # Process Resume file/image via extraction if uploaded
        if resume_image and resume_image.filename:
            try:
                extracted_resume_text = extract_text_from_resume_image(resume_image)
                resume_text = "\n".join(filter(None, (resume_text, extracted_resume_text)))
            except ResumeImageError as err:
                flash(f"Resume upload error: {err}")

        if not job_description:
            flash("Please provide a job description by pasting text or uploading a document/screenshot.")
        elif not resume_text:
            flash("Please provide your resume by pasting text or uploading a PDF, DOCX, or image.")
        else:
            analysis = analyze_job(job_description, resume_text)
            record_activity(session["user_id"], "job", "Job match analysis", analysis["match_score"])

    return render_template(
        "job_analyzer.html",
        analysis=analysis,
        job_description=job_description,
        resume_text=resume_text
    )


@jobs_bp.route("/jobs/bridge-to-builder", methods=["POST", "GET"])
def bridge_to_builder():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    missing_keywords_str = request.form.get("missing_keywords", "") or request.args.get("missing", "")
    matched_skills_str = request.form.get("matched_skills", "") or request.args.get("matched", "")
    job_description = request.form.get("job_description", "") or request.args.get("jd", "")
    resume_text = request.form.get("resume_text", "") or request.args.get("resume", "")

    # Parse lists
    missing_list = [k.strip() for k in missing_keywords_str.split(",") if k.strip()]
    matched_list = [k.strip() for k in matched_skills_str.split(",") if k.strip()]

    # Extract ALL details from the given resume and job context (contact, role, exp, edu, projects, skills)
    from ai.gemini_client import gemini_parse_resume_for_builder
    prefill_data = gemini_parse_resume_for_builder(
        resume_text=resume_text,
        job_description=job_description,
        missing_keywords=missing_list,
        matched_skills=matched_list
    )

    prefill_data["missing_keywords"] = missing_list
    prefill_data["from_job_analyzer"] = True

    # Save in both session and server memory cache for 100% resilience
    session["builder_prefill"] = prefill_data
    try:
        from routes.builder import set_builder_prefill
        set_builder_prefill(session.get("user_id"), prefill_data)
    except Exception:
        pass

    return redirect(url_for("builder.builder_view"))

