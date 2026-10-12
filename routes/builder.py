from datetime import datetime, timezone
import json
import logging

from flask import Blueprint, flash, jsonify, redirect, render_template, request, send_file, session, url_for

from ai.gemini_client import (
    gemini_build_resume_from_scratch,
    gemini_extract_certificate_info,
    gemini_improve_bullet,
    gemini_match_job_description,
    gemini_resume_xray,
)
from ai.resume_ai import ResumeImageError, extract_text_from_file
from db import get_db, record_activity
from services.docx_exporter import generate_resume_docx
from services.limiter import limiter
from services.security import login_required, sanitize_text

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
@login_required
def builder_view():
    user_id = session.get("user_id")
    saved_prefill = session.pop("builder_prefill", None) or get_builder_prefill(user_id) or {}

    current_user_obj = session.get("user")
    user_name_fallback = ""
    if isinstance(current_user_obj, dict):
        user_name_fallback = current_user_obj.get("name", "")
    elif isinstance(current_user_obj, str):
        user_name_fallback = current_user_obj

    prefill = {
        "name": sanitize_text(request.args.get("name") or saved_prefill.get("name") or user_name_fallback, max_length=150),
        "target_role": sanitize_text(request.args.get("role") or saved_prefill.get("target_role", ""), max_length=150),
        "experience_level": sanitize_text(request.args.get("level") or saved_prefill.get("experience_level", "Mid-Level"), max_length=50),
        "industry": sanitize_text(request.args.get("industry") or saved_prefill.get("industry", "Technology & Software"), max_length=100),
        "email": sanitize_text(request.args.get("email") or saved_prefill.get("email", ""), max_length=254),
        "phone": sanitize_text(request.args.get("phone") or saved_prefill.get("phone", ""), max_length=50),
        "linkedin": sanitize_text(request.args.get("linkedin") or saved_prefill.get("linkedin", ""), max_length=255),
        "skills": sanitize_text(request.args.get("skills") or saved_prefill.get("skills", ""), max_length=2000),
        "experience_raw": sanitize_text(saved_prefill.get("experience_raw", ""), max_length=15000),
        "education_raw": sanitize_text(request.args.get("education") or saved_prefill.get("education_raw", ""), max_length=5000),
        "projects_raw": sanitize_text(request.args.get("projects") or saved_prefill.get("projects_raw", ""), max_length=8000),
        "missing_keywords": saved_prefill.get("missing_keywords", []),
        "from_job_analyzer": saved_prefill.get("from_job_analyzer", False),
    }
    return render_template("builder.html", prefill=prefill, resume=None)


@builder_bp.post("/builder/upload-certificate")
@login_required
@limiter.limit("20 per minute")
def upload_certificate():
    """Extract and parse professional certificates from PDF, DOCX, DOC, Images (PNG/JPG/WEBP), or TXT."""

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
@login_required
@limiter.limit("15 per minute")
def generate_resume():
    data = {
        "name": sanitize_text(request.form.get("name", "").strip(), max_length=150) or session.get("user", "Candidate"),
        "email": sanitize_text(request.form.get("email", "").strip(), max_length=254),
        "phone": sanitize_text(request.form.get("phone", "").strip(), max_length=50),
        "location": sanitize_text(request.form.get("location", "").strip(), max_length=150),
        "linkedin": sanitize_text(request.form.get("linkedin", "").strip(), max_length=255),
        "target_role": sanitize_text(request.form.get("target_role", "").strip(), max_length=150) or "Software Engineer",
        "experience_level": sanitize_text(request.form.get("experience_level", "Mid-Senior"), max_length=50),
        "industry": sanitize_text(request.form.get("industry", "Technology"), max_length=100),
        "skills": sanitize_text(request.form.get("skills", "").strip(), max_length=2000),
        "experience_raw": sanitize_text(request.form.get("experience_raw", "").strip(), max_length=15000),
        "education_raw": sanitize_text(request.form.get("education_raw", "").strip(), max_length=5000),
        "projects_raw": sanitize_text(request.form.get("projects_raw", "").strip(), max_length=8000),
    }

    fresher_mode = request.form.get("fresher_mode") in ("true", "1", "True")
    data["fresher_mode"] = fresher_mode

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
                        extracted_certs.append(sanitize_text(info["formatted_entry"], max_length=300))
                except Exception as e:
                    logger.warning(f"Could not parse multipart cert {cert_file.filename}: {e}")

    if extracted_certs:
        existing_projects = data["projects_raw"]
        joined_certs = " · ".join(extracted_certs)
        if existing_projects:
            data["projects_raw"] = f"{existing_projects}, {joined_certs}"
        else:
            data["projects_raw"] = joined_certs

    strategy = sanitize_text(request.form.get("strategy", "metric_driven"), max_length=50)
    try:
        variation_seed = int(request.form.get("variation_seed", 1))
    except (ValueError, TypeError):
        variation_seed = 1

    generated = gemini_build_resume_from_scratch(data, strategy=strategy, variation_seed=variation_seed)
    session["last_generated_resume"] = generated

    record_activity(
        session["user_id"],
        "resume_builder",
        f"Resume Builder: {data['target_role']} (Gen #{variation_seed} · {generated.get('strategy_title', strategy)})",
        generated.get("ats_score", 97),
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return {"status": "ok", "resume": generated}

    return render_template("builder.html", prefill=data, resume=generated, active_strategy=strategy, current_seed=variation_seed)


@builder_bp.post("/builder/improve-bullet")
@login_required
@limiter.limit("30 per minute")
def improve_bullet():
    """Rewrite weak bullet points using action verbs & metrics without inventing facts."""
    payload = request.get_json(silent=True) or request.form
    bullet = sanitize_text(payload.get("bullet", "").strip(), max_length=2000)
    role = sanitize_text(payload.get("role", "").strip(), max_length=150)
    industry = sanitize_text(payload.get("industry", "").strip(), max_length=150)

    if not bullet:
        return {"success": False, "error": "No bullet text provided"}, 400

    try:
        result = gemini_improve_bullet(bullet, role=role, industry=industry)
        return {"success": True, "result": result}
    except Exception as exc:
        logger.error(f"Error improving bullet: {exc}")
        return {"success": False, "error": str(exc)}, 500


@builder_bp.post("/builder/match-jd")
@login_required
@limiter.limit("20 per minute")
def match_jd():
    """Highlight matched and missing keywords for a target job description."""
    payload = request.get_json(silent=True) or request.form
    jd_text = sanitize_text(payload.get("jd_text", "").strip(), max_length=10000)
    skills = sanitize_text(payload.get("skills", "").strip(), max_length=3000)
    resume_text = sanitize_text(payload.get("resume_text", "").strip(), max_length=15000)

    if not jd_text:
        return {"success": False, "error": "Job description text is required"}, 400

    try:
        result = gemini_match_job_description(jd_text, resume_skills=skills, resume_text=resume_text)
        return {"success": True, "result": result}
    except Exception as exc:
        logger.error(f"Error matching job description: {exc}")
        return {"success": False, "error": str(exc)}, 500


@builder_bp.post("/builder/xray")
@login_required
@limiter.limit("20 per minute")
def resume_xray():
    """Explain the strongest and weakest parts of the candidate's resume."""
    payload = request.get_json(silent=True) or {}
    resume_data = payload.get("resume") or session.get("last_generated_resume")
    if not resume_data:
        return {"success": False, "error": "No resume data available for X-Ray audit"}, 400

    try:
        result = gemini_resume_xray(resume_data)
        return {"success": True, "result": result}
    except Exception as exc:
        logger.error(f"Error performing resume X-Ray: {exc}")
        return {"success": False, "error": str(exc)}, 500


@builder_bp.post("/builder/save-version")
@login_required
@limiter.limit("30 per minute")
def save_version():
    """Save a job-specific resume draft/version for ATS comparison."""
    payload = request.get_json(silent=True) or {}
    version_name = sanitize_text(payload.get("version_name", "").strip(), max_length=150) or f"Draft {datetime.now().strftime('%b %d, %H:%M')}"
    target_role = sanitize_text(payload.get("target_role", "").strip(), max_length=150) or "Software Engineer"
    try:
        ats_score = int(payload.get("ats_score", 95))
    except (ValueError, TypeError):
        ats_score = 95
    strategy = sanitize_text(payload.get("strategy", "metric_driven"), max_length=50)
    resume_data = payload.get("resume_data")

    if not resume_data:
        resume_data = session.get("last_generated_resume")

    if not resume_data:
        return {"success": False, "error": "No resume data to save"}, 400

    user_id = session["user_id"]
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO resume_versions (user_id, version_name, target_role, ats_score, strategy, resume_data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, version_name, target_role, ats_score, strategy, json.dumps(resume_data), now_iso)
        )
        db.commit()
        version_id = cursor.lastrowid

        record_activity(
            user_id,
            "resume_version",
            f"Saved Resume Version: {version_name} ({target_role})",
            ats_score
        )

        return {"success": True, "version_id": version_id, "version_name": version_name}
    except Exception as exc:
        logger.error(f"Failed to save resume version: {exc}")
        return {"success": False, "error": str(exc)}, 500


@builder_bp.get("/builder/versions")
@login_required
def get_versions():
    """Retrieve saved resume versions for comparison."""
    user_id = session["user_id"]
    try:
        db = get_db()
        rows = db.execute(
            """
            SELECT id, version_name, target_role, ats_score, strategy, resume_data, created_at
            FROM resume_versions
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,)
        ).fetchall()

        versions = []
        for r in rows:
            try:
                res_obj = json.loads(r["resume_data"])
            except Exception:
                res_obj = {}
            versions.append({
                "id": r["id"],
                "version_name": r["version_name"],
                "target_role": r["target_role"],
                "ats_score": r["ats_score"],
                "strategy": r["strategy"],
                "resume_data": res_obj,
                "created_at": r["created_at"]
            })

        return {"success": True, "versions": versions}
    except Exception as exc:
        logger.error(f"Failed to fetch versions: {exc}")
        return {"success": False, "error": str(exc)}, 500


@builder_bp.post("/builder/delete-version")
@login_required
def delete_version():
    """Delete a saved resume version with ownership verification."""
    payload = request.get_json(silent=True) or request.form
    raw_id = payload.get("version_id")
    if not raw_id:
        return {"success": False, "error": "Version ID required"}, 400

    try:
        version_id = int(raw_id)
    except (ValueError, TypeError):
        return {"success": False, "error": "Invalid version ID format"}, 400

    user_id = session["user_id"]
    try:
        db = get_db()
        db.execute("DELETE FROM resume_versions WHERE id = ? AND user_id = ?", (version_id, user_id))
        db.commit()
        return {"success": True}
    except Exception as exc:
        logger.error(f"Failed to delete version: {exc}")
        return {"success": False, "error": str(exc)}, 500


@builder_bp.post("/builder/export-docx")
@login_required
@limiter.limit("30 per minute")
def export_docx():
    """Native ATS-compliant Microsoft Word (.docx) export preserving format and margins."""
    payload = request.get_json(silent=True) or {}
    resume_data = payload.get("resume")
    template_style = sanitize_text(payload.get("template") or request.form.get("template") or "classic", max_length=50)

    if not resume_data and request.form.get("resume_json"):
        try:
            resume_data = json.loads(request.form.get("resume_json"))
        except Exception:
            resume_data = None

    if not resume_data:
        resume_data = session.get("last_generated_resume")

    if not resume_data:
        return {"success": False, "error": "No resume data available for DOCX export"}, 400

    try:
        stream = generate_resume_docx(resume_data, template_style=template_style)
        candidate_name = resume_data.get("candidate_name") or "Candidate"
        clean_name = "".join(c for c in candidate_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        filename = f"{clean_name}_Resume_{template_style.capitalize()}.docx"

        return send_file(
            stream,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as exc:
        logger.error(f"DOCX export error: {exc}")
        return {"success": False, "error": f"Failed to generate DOCX: {str(exc)}"}, 500



