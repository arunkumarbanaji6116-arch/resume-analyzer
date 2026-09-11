from datetime import datetime, timezone
import logging

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ai.gemini_client import gemini_build_resume_from_scratch, gemini_extract_certificate_info
from ai.resume_ai import ResumeImageError, extract_text_from_file
from db import get_db, record_activity

logger = logging.getLogger(__name__)

builder_bp = Blueprint("builder", __name__)

ALLOWED_CERT_EXTENSIONS = {"pdf", "docx", "doc", "txt", "rtf", "png", "jpg", "jpeg", "webp"}


_BUILDER_PREFILL_STORE = {}


def set_builder_prefill(user_id, data: dict):
    if user_id:
        _BUILDER_PREFILL_STORE[user_id] = dict(data)


def get_builder_prefill(user_id):
    if user_id and user_id in _BUILDER_PREFILL_STORE:
        return _BUILDER_PREFILL_STORE.pop(user_id, {})
    return {}


@builder_bp.get("/builder")
def builder_view():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")
    saved_prefill = session.pop("builder_prefill", None) or get_builder_prefill(user_id) or {}

    current_user_obj = session.get("user")
    user_name_fallback = ""
    if isinstance(current_user_obj, dict):
        user_name_fallback = current_user_obj.get("name", "")
    elif isinstance(current_user_obj, str):
        user_name_fallback = current_user_obj

    prefill = {
        "name": request.args.get("name") or saved_prefill.get("name") or user_name_fallback,
        "target_role": request.args.get("role") or saved_prefill.get("target_role", ""),
        "experience_level": request.args.get("level") or saved_prefill.get("experience_level", "Mid-Level"),
        "industry": request.args.get("industry") or saved_prefill.get("industry", "Technology & Software"),
        "email": request.args.get("email") or saved_prefill.get("email", ""),
        "phone": request.args.get("phone") or saved_prefill.get("phone", ""),
        "linkedin": request.args.get("linkedin") or saved_prefill.get("linkedin", ""),
        "skills": request.args.get("skills") or saved_prefill.get("skills", ""),
        "experience_raw": saved_prefill.get("experience_raw", ""),
        "education_raw": request.args.get("education") or saved_prefill.get("education_raw", ""),
        "projects_raw": request.args.get("projects") or saved_prefill.get("projects_raw", ""),
        "missing_keywords": saved_prefill.get("missing_keywords", []),
        "from_job_analyzer": saved_prefill.get("from_job_analyzer", False),
    }
    return render_template("builder.html", prefill=prefill, resume=None)


@builder_bp.post("/builder/upload-certificate")
def upload_certificate():
    """Extract and parse professional certificates from PDF, DOCX, DOC, Images (PNG/JPG/WEBP), or TXT."""
    if "user_id" not in session:
        return {"success": False, "error": "Authentication required"}, 401

    uploaded_file = request.files.get("file") or request.files.get("certificate_file")
    if not uploaded_file or not uploaded_file.filename:
        return {"success": False, "error": "No file provided. Please select a certificate file to upload."}, 400

    filename = uploaded_file.filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_CERT_EXTENSIONS:
        return {
            "success": False,
            "error": f"Unsupported file format (.{ext}). Eligible formats: PDF, PNG, JPG, JPEG, WEBP, DOCX, DOC, TXT, RTF"
        }, 400

    try:
        raw_text = extract_text_from_file(uploaded_file)
        cert_info = gemini_extract_certificate_info(raw_text, filename)

        # File size calculation
        uploaded_file.seek(0, 2)
        size_bytes = uploaded_file.tell()
        uploaded_file.seek(0)

        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes // 1024} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

        return {
            "success": True,
            "filename": filename,
            "filesize": size_str,
            "certificate_name": cert_info.get("title", ""),
            "issuer": cert_info.get("issuer", ""),
            "year": cert_info.get("year", ""),
            "formatted_entry": cert_info.get("formatted_entry", cert_info.get("title", filename)),
            "raw_text": raw_text[:300] if raw_text else ""
        }
    except ResumeImageError as rie:
        logger.warning(f"Certificate extraction error: {rie}")
        return {"success": False, "error": str(rie)}, 400
    except Exception as exc:
        logger.error(f"Unexpected certificate processing error: {exc}")
        return {"success": False, "error": f"Could not process certificate: {str(exc)}"}, 500


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

    # Handle any directly attached certificate files via multipart POST
    uploaded_files = request.files.getlist("certificate_files") or []
    single_file = request.files.get("certificate_file")
    if single_file and single_file not in uploaded_files:
        uploaded_files.append(single_file)

    extracted_certs = []
    for cert_file in uploaded_files:
        if cert_file and cert_file.filename:
            ext = cert_file.filename.rsplit(".", 1)[-1].lower() if "." in cert_file.filename else ""
            if ext in ALLOWED_CERT_EXTENSIONS:
                try:
                    txt = extract_text_from_file(cert_file)
                    info = gemini_extract_certificate_info(txt, cert_file.filename)
                    if info.get("formatted_entry"):
                        extracted_certs.append(info["formatted_entry"])
                except Exception as e:
                    logger.warning(f"Could not parse multipart cert {cert_file.filename}: {e}")

    if extracted_certs:
        existing_projects = data["projects_raw"]
        joined_certs = " · ".join(extracted_certs)
        if existing_projects:
            data["projects_raw"] = f"{existing_projects}, {joined_certs}"
        else:
            data["projects_raw"] = joined_certs

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


