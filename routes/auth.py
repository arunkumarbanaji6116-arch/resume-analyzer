from datetime import datetime, timedelta, timezone
import logging
import os
import re
import secrets

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
import requests
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from db import get_db, log_security_event
from services.limiter import limiter
from services.security import is_safe_url, sanitize_text, validate_password_strength
from services.smtp_service import (
    is_smtp_configured,
    send_github_otp_email,
    send_otp_email,
    send_password_reset_email,
)
from services.supabase_service import (
    supabase_create_user,
    supabase_get_user_by_email,
    supabase_update_password,
    supabase_save_otp,
    supabase_verify_otp,
    supabase_delete_otps,
)

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


def _derive_name_from_email(email: str) -> str:
    local_part = (email or "").split("@")[0]
    tokens = [t.capitalize() for t in re.split(r"[._-]+", local_part) if t]
    return " ".join(tokens) or "Member"


def _row_to_dict(row) -> dict:
    if not row:
        return {}
    if isinstance(row, dict):
        return row
    try:
        return dict(row)
    except Exception:
        return {}


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute; 60 per hour")
def login():
    next_url = request.args.get("next", "")
    if request.method == "POST":
        email = sanitize_text(request.form.get("email", ""), max_length=120).lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
        user_dict = _row_to_dict(user)

        # If not found locally or local password doesn't match, check Supabase for newer/synced record
        if not user_dict or not check_password_hash(user_dict.get("password_hash", ""), password):
            sb_user = supabase_get_user_by_email(email)
            if sb_user:
                try:
                    if user_dict:
                        db.execute(
                            "UPDATE users SET name = ?, password_hash = ? WHERE lower(email) = ?",
                            (sb_user.get("name") or user_dict.get("name"), sb_user.get("password_hash", ""), email),
                        )
                    else:
                        db.execute(
                            "INSERT OR IGNORE INTO users (id, name, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                            (
                                sb_user.get("id"),
                                sb_user.get("name") or _derive_name_from_email(email),
                                email,
                                sb_user.get("password_hash", ""),
                                sb_user.get("created_at") or datetime.now(timezone.utc).isoformat(),
                            ),
                        )
                    db.commit()
                    user = db.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
                    user_dict = _row_to_dict(user) or sb_user
                except Exception:
                    user_dict = sb_user

        authenticated = False
        if user_dict and check_password_hash(user_dict.get("password_hash", ""), password):
            authenticated = True
        elif (
            user_dict
            and user_dict.get("password_hash") in ("google_smtp_verified", "github_verified", "github_oauth_verified")
            and validate_password_strength(password)[0]
        ):
            # Upgrade SSO-only account to also support password login
            new_hash = generate_password_hash(password)
            try:
                db.execute("UPDATE users SET password_hash = ? WHERE lower(email) = ?", (new_hash, email))
                db.commit()
                supabase_update_password(email, new_hash)
            except Exception:
                pass
            authenticated = True
        elif not user_dict and "@" in email and "." in email and validate_password_strength(password)[0]:
            # Auto-provision if serverless SQLite cold-started or user signs in directly
            now_iso = datetime.now(timezone.utc).isoformat()
            pwd_hash = generate_password_hash(password)
            derived_name = _derive_name_from_email(email)
            try:
                cursor = db.execute(
                    "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                    (derived_name, email, pwd_hash, now_iso),
                )
                db.commit()
                user_id = cursor.lastrowid
                sb_user = supabase_create_user(derived_name, email, pwd_hash, now_iso)
                if sb_user and sb_user.get("id"):
                    user_id = sb_user["id"]
                user_dict = {"id": user_id, "name": derived_name, "email": email, "is_admin": 0}
                authenticated = True
            except Exception:
                pass

        if authenticated and user_dict:
            session.permanent = bool(remember)
            session["user_id"] = user_dict["id"]
            session["user"] = user_dict.get("name") or _derive_name_from_email(email)
            session["is_admin"] = bool(user_dict.get("is_admin", 0))

            target = next_url if is_safe_url(next_url) else url_for("dashboard")
            resp = redirect(target)
            if remember:
                resp.set_cookie(
                    "remember_email",
                    email,
                    max_age=30 * 86400,
                    samesite="Lax",
                    httponly=True,
                    secure=Config.SESSION_COOKIE_SECURE,
                )
            else:
                resp.delete_cookie("remember_email")
            return resp

        if user_dict and user_dict.get("password_hash") in ("google_smtp_verified", "github_verified", "github_oauth_verified"):
            flash("This account was created with SSO. Click Google or GitHub below to log in.", "error")
        else:
            flash("Email or password is incorrect.", "error")
            log_security_event("failed_login_attempt", f"Email: {email}")

        return render_template("login.html", email=email, password=password if remember else "", remember=remember)

    remember_email = request.args.get("email") or request.cookies.get("remember_email", "")
    return render_template("login.html", email=remember_email, remember=bool(remember_email))


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("8 per minute; 40 per hour")
def register():
    if request.method == "GET":
        return redirect(url_for("auth.login", mode="signup"))
    name = sanitize_text(request.form.get("name", ""), max_length=80)
    email = sanitize_text(request.form.get("email", ""), max_length=120).lower()
    password = request.form.get("password", "")

    if not name or not email or "@" not in email:
        flash("Please enter your name and a valid email address.", "error")
        return redirect(url_for("auth.login", mode="signup"))

    is_valid_pwd, pwd_err = validate_password_strength(password)
    if not is_valid_pwd:
        flash(pwd_err, "error")
        return redirect(url_for("auth.login", mode="signup"))

    try:
        db = get_db()
        now_iso = datetime.now(timezone.utc).isoformat()
        pwd_hash = generate_password_hash(password)

        existing = db.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
        existing_dict = _row_to_dict(existing)
        if not existing_dict:
            sb_existing = supabase_get_user_by_email(email)
            if sb_existing:
                existing_dict = sb_existing

        if existing_dict:
            # Update existing user or log them right in without blocking on duplicate email
            user_id = existing_dict.get("id")
            user_name = name or existing_dict.get("name") or _derive_name_from_email(email)
            is_admin = bool(existing_dict.get("is_admin", 0))
            if not existing:
                db.execute(
                    "INSERT OR IGNORE INTO users (id, name, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, user_name, email, pwd_hash, existing_dict.get("created_at") or now_iso),
                )
                db.commit()
            if not check_password_hash(existing_dict.get("password_hash", ""), password):
                db.execute(
                    "UPDATE users SET name = ?, password_hash = ? WHERE lower(email) = ?",
                    (user_name, pwd_hash, email),
                )
                db.commit()
                supabase_create_user(user_name, email, pwd_hash, existing_dict.get("created_at") or now_iso)
            row = db.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
            if row:
                user_id = row["id"]
                is_admin = bool(row["is_admin"])
        else:
            cursor = db.execute(
                "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (name, email, pwd_hash, now_iso),
            )
            db.commit()
            user_id = cursor.lastrowid
            user_name = name
            is_admin = False

            # Sync user to Supabase
            sb_user = supabase_create_user(name, email, pwd_hash, now_iso)
            if sb_user and sb_user.get("id"):
                user_id = sb_user["id"]

        session.permanent = True
        session["user_id"] = user_id
        session["user"] = user_name
        session["is_admin"] = is_admin
        resp = redirect(url_for("dashboard"))
        resp.set_cookie(
            "remember_email",
            email,
            max_age=30 * 86400,
            samesite="Lax",
            httponly=True,
            secure=Config.SESSION_COOKIE_SECURE,
        )
        return resp
    except Exception as exc:
        logger.error(f"[AUTH ERROR] Registration error for {email}: {exc}")
        flash("Unable to complete sign up right now. Please try signing in.", "error")
        return redirect(url_for("auth.login", email=email))


def _format_email_error(status_or_msg: str) -> str:
    if status_or_msg == "dev_mode":
        return "Email service not configured in .env. Please configure RESEND_API_KEY in your .env file."
    if "You can only send testing emails to your own email address" in status_or_msg:
        return (
            "Resend testing mode restriction: Verification emails can only be delivered to your registered account "
            "(arunkumarbanaji6116@gmail.com). To send to other addresses, please verify a custom domain at resend.com."
        )
    return f"Email delivery failed: {status_or_msg}. Please check your Resend configuration."


@auth_bp.route("/google-otp/send", methods=["POST"])
@auth_bp.route("/auth/google-otp/send", methods=["POST"])
@limiter.limit("5 per minute; 25 per hour")
def send_google_otp():
    data = request.get_json(silent=True) or request.form
    email = sanitize_text(data.get("email") or "", max_length=120).lower()

    if not email or "@" not in email or "." not in email:
        return jsonify({"success": False, "message": "Please enter a valid Google email address."}), 400

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    now = datetime.now(timezone.utc)
    # Generous 30-minute validity window so users are never rushed
    expires_at = (now + timedelta(minutes=30)).isoformat()
    now_iso = now.isoformat()

    try:
        db = get_db()
        # Clean up only expired OTPs for this email, keeping recent codes valid in case of resend
        db.execute("DELETE FROM email_otps WHERE email = ? AND expires_at < ?", (email, now_iso))
        db.execute(
            "INSERT INTO email_otps (email, otp_code, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (email, otp_code, expires_at, now_iso),
        )
        db.commit()
        supabase_save_otp(email, otp_code, expires_at, now_iso)
    except Exception as exc:
        return jsonify({"success": False, "message": f"Database error storing OTP: {exc}"}), 500

    session["google_auth_email"] = email

    sent, status_or_msg = send_otp_email(email, otp_code)

    if sent:
        return jsonify({
            "success": True,
            "is_dev_mode": False,
            "message": f"Verification code sent to {email}. Please check your inbox.",
        })
    else:
        # Email delivery failed
        logger.error(f"[AUTH ERROR] Failed to deliver OTP to {email}: {status_or_msg}")
        return jsonify({
            "success": False,
            "is_dev_mode": False,
            "message": _format_email_error(status_or_msg),
        }), 400


@auth_bp.route("/google-otp/verify", methods=["POST"])
@auth_bp.route("/auth/google-otp/verify", methods=["POST"])
@limiter.limit("10 per minute; 50 per hour")
def verify_google_otp():
    data = request.get_json(silent=True) or request.form
    email = sanitize_text(data.get("email") or session.get("google_auth_email") or "", max_length=120).lower()
    otp_code = (data.get("otp") or "").strip()
    clean_otp = re.sub(r"[^0-9]", "", otp_code)

    if not email or len(clean_otp) != 6:
        return jsonify({"success": False, "message": "Email and 6-digit verification code are required."}), 400

    now_iso = datetime.now(timezone.utc).isoformat()
    db = get_db()
    record = db.execute(
        "SELECT * FROM email_otps WHERE email = ? AND otp_code = ? AND expires_at >= ?",
        (email, clean_otp, now_iso),
    ).fetchone()

    sb_valid = False
    if not record:
        sb_valid = supabase_verify_otp(email, clean_otp)

    if not record and not sb_valid:
        # Check if the code expired
        expired_record = db.execute(
            "SELECT * FROM email_otps WHERE email = ? AND otp_code = ?",
            (email, clean_otp),
        ).fetchone()
        if expired_record:
            return jsonify({
                "success": False,
                "message": "This verification code has expired. Please click 'Resend code' to receive a fresh code.",
            }), 400

        # Check if there is an active OTP for this email
        has_active = db.execute(
            "SELECT * FROM email_otps WHERE email = ? AND expires_at >= ?",
            (email, now_iso),
        ).fetchone()
        if has_active:
            return jsonify({
                "success": False,
                "message": "Incorrect 6-digit code. Please check the newest email sent to your inbox.",
            }), 400

        return jsonify({
            "success": False,
            "message": "No active verification code found for this email. Please click 'Resend code'.",
        }), 400

    # Verification successful: clear all OTPs for this email locally & in Supabase
    db.execute("DELETE FROM email_otps WHERE email = ?", (email,))
    db.commit()
    supabase_delete_otps(email)

    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        sb_user = supabase_get_user_by_email(email)
        if sb_user:
            user = sb_user

    if not user:
        local_part = email.split("@")[0]
        tokens = [t.capitalize() for t in re.split(r"[._-]+", local_part) if t]
        name = " ".join(tokens) or "Google User"
        now_dt = datetime.now(timezone.utc).isoformat()
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, "google_smtp_verified", now_dt),
        )
        db.commit()
        user_id = cursor.lastrowid
        user_name = name

        sb_created = supabase_create_user(name, email, "google_smtp_verified", now_dt)
        if sb_created and sb_created.get("id"):
            user_id = sb_created["id"]
    else:
        user_id = user["id"]
        user_name = user["name"]

    session.permanent = True
    session["user_id"] = user_id
    session["user"] = user_name
    session.pop("google_auth_email", None)

    resp = jsonify({
        "success": True,
        "redirect_url": url_for("dashboard"),
        "user_name": user_name,
    })
    resp.set_cookie("remember_email", email, max_age=30 * 86400, samesite="Lax")
    return resp


@auth_bp.route("/github-otp/send", methods=["POST"])
@auth_bp.route("/auth/github-otp/send", methods=["POST"])
@limiter.limit("5 per minute; 25 per hour")
def send_github_otp():
    data = request.get_json(silent=True) or request.form
    raw_input = sanitize_text(data.get("identifier") or data.get("email") or "", max_length=120)

    if not raw_input:
        return jsonify({"success": False, "message": "Please enter your GitHub email address or username."}), 400

    target_email = ""
    github_name = ""

    if "@" in raw_input and "." in raw_input:
        target_email = raw_input.lower()
    else:
        # User provided GitHub username
        gh_user = raw_input.lstrip("@")
        try:
            gh_res = requests.get(
                f"https://api.github.com/users/{gh_user}",
                headers={"User-Agent": "CareerForge-AI"},
                timeout=4,
            )
            if gh_res.status_code == 200:
                gh_info = gh_res.json()
                target_email = (gh_info.get("email") or "").strip().lower()
                github_name = gh_info.get("name") or gh_info.get("login") or gh_user
            elif gh_res.status_code == 404:
                return jsonify({"success": False, "message": f"GitHub user '@{gh_user}' not found. Please enter your GitHub email."}), 404
        except Exception:
            pass

        if not target_email:
            return jsonify({
                "success": False,
                "need_email": True,
                "message": f"GitHub user '@{gh_user}' has a private email. Please enter your GitHub email address below.",
            }), 200

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=30)).isoformat()
    now_iso = now.isoformat()

    try:
        db = get_db()
        db.execute("DELETE FROM email_otps WHERE email = ? AND expires_at < ?", (target_email, now_iso))
        db.execute(
            "INSERT INTO email_otps (email, otp_code, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (target_email, otp_code, expires_at, now_iso),
        )
        db.commit()
        supabase_save_otp(target_email, otp_code, expires_at, now_iso)
    except Exception as exc:
        return jsonify({"success": False, "message": f"Database error storing OTP: {exc}"}), 500

    session["github_auth_email"] = target_email
    if github_name:
        session["github_auth_name"] = github_name

    sent, status_or_msg = send_github_otp_email(target_email, otp_code)
    if sent:
        return jsonify({
            "success": True,
            "email": target_email,
            "message": f"GitHub verification code successfully sent to {target_email}. Please check your inbox.",
        })
    else:
        return jsonify({
            "success": False,
            "message": _format_email_error(status_or_msg),
        }), 400


@auth_bp.route("/github-otp/verify", methods=["POST"])
@auth_bp.route("/auth/github-otp/verify", methods=["POST"])
@limiter.limit("10 per minute; 50 per hour")
def verify_github_otp():
    data = request.get_json(silent=True) or request.form
    email = sanitize_text(data.get("email") or session.get("github_auth_email") or "", max_length=120).lower()
    otp_code = (data.get("otp") or "").strip()
    clean_otp = re.sub(r"[^0-9]", "", otp_code)

    if not email or len(clean_otp) != 6:
        return jsonify({"success": False, "message": "Email and 6-digit verification code are required."}), 400

    now_iso = datetime.now(timezone.utc).isoformat()
    db = get_db()
    record = db.execute(
        "SELECT * FROM email_otps WHERE email = ? AND otp_code = ? AND expires_at >= ?",
        (email, clean_otp, now_iso),
    ).fetchone()

    sb_valid = False
    if not record:
        sb_valid = supabase_verify_otp(email, clean_otp)

    if not record and not sb_valid:
        expired_record = db.execute(
            "SELECT * FROM email_otps WHERE email = ? AND otp_code = ?",
            (email, clean_otp),
        ).fetchone()
        if expired_record:
            return jsonify({
                "success": False,
                "message": "This verification code has expired. Please click 'Resend code' to get a fresh code.",
            }), 400

        has_active = db.execute(
            "SELECT * FROM email_otps WHERE email = ? AND expires_at >= ?",
            (email, now_iso),
        ).fetchone()
        if has_active:
            return jsonify({
                "success": False,
                "message": "Incorrect 6-digit code. Please check the newest email sent to your inbox.",
            }), 400

        return jsonify({
            "success": False,
            "message": "No active verification code found for this email. Please click 'Resend code'.",
        }), 400

    db.execute("DELETE FROM email_otps WHERE email = ?", (email,))
    db.commit()
    supabase_delete_otps(email)

    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        sb_user = supabase_get_user_by_email(email)
        if sb_user:
            user = sb_user

    if not user:
        name = session.get("github_auth_name")
        if not name:
            local_part = email.split("@")[0]
            tokens = [t.capitalize() for t in re.split(r"[._-]+", local_part) if t]
            name = " ".join(tokens) or "GitHub User"
        now_dt = datetime.now(timezone.utc).isoformat()
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, "github_verified", now_dt),
        )
        db.commit()
        user_id = cursor.lastrowid
        user_name = name

        sb_created = supabase_create_user(name, email, "github_verified", now_dt)
        if sb_created and sb_created.get("id"):
            user_id = sb_created["id"]
    else:
        user_id = user["id"]
        user_name = user["name"]

    session.permanent = True
    session["user_id"] = user_id
    session["user"] = user_name
    session.pop("github_auth_email", None)
    session.pop("github_auth_name", None)

    resp = jsonify({
        "success": True,
        "redirect_url": url_for("dashboard"),
        "user_name": user_name,
    })
    resp.set_cookie("remember_email", email, max_age=30 * 86400, samesite="Lax")
    return resp


@auth_bp.route("/github", methods=["GET"])
@auth_bp.route("/auth/github", methods=["GET"])
def github_oauth_redirect():
    client_id = os.getenv("GITHUB_CLIENT_ID")
    if not client_id:
        return redirect(url_for("auth.login") + "?trigger=github")
    redirect_uri = url_for("auth.github_oauth_callback", _external=True)
    state = secrets.token_urlsafe(16)
    session["github_oauth_state"] = state
    gh_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=user:email&state={state}"
    return redirect(gh_url)


@auth_bp.route("/github/callback", methods=["GET"])
@auth_bp.route("/auth/github/callback", methods=["GET"])
def github_oauth_callback():
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    code = request.args.get("code")

    if not code or not client_id or not client_secret:
        flash("GitHub authentication failed or was canceled.", "error")
        return redirect(url_for("auth.login"))

    token_resp = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={"client_id": client_id, "client_secret": client_secret, "code": code},
        timeout=8,
    )
    if not token_resp.ok:
        flash("Failed to obtain access token from GitHub.", "error")
        return redirect(url_for("auth.login"))

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        flash("GitHub authorization was not granted.", "error")
        return redirect(url_for("auth.login"))

    user_resp = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {access_token}", "User-Agent": "CareerForge-AI"},
        timeout=8,
    )
    user_data = user_resp.json() if user_resp.ok else {}
    email = (user_data.get("email") or "").strip().lower()

    if not email:
        emails_resp = requests.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"token {access_token}", "User-Agent": "CareerForge-AI"},
            timeout=8,
        )
        if emails_resp.ok:
            for item in emails_resp.json():
                if item.get("primary") and item.get("verified"):
                    email = item.get("email", "").strip().lower()
                    break
            if not email and emails_resp.json():
                email = emails_resp.json()[0].get("email", "").strip().lower()

    if not email:
        flash("Could not retrieve a verified email from your GitHub account.", "error")
        return redirect(url_for("auth.login"))

    name = user_data.get("name") or user_data.get("login") or "GitHub User"
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        now_dt = datetime.now(timezone.utc).isoformat()
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, "github_oauth_verified", now_dt),
        )
        db.commit()
        user_id = cursor.lastrowid
        user_name = name
    else:
        user_id = user["id"]
        user_name = user["name"]

    session.permanent = True
    session["user_id"] = user_id
    session["user"] = user_name

    resp = redirect(url_for("dashboard"))
    resp.set_cookie("remember_email", email, max_age=30 * 86400, samesite="Lax")
    return resp


@auth_bp.route("/forgot-password/send", methods=["POST"])
@auth_bp.route("/auth/forgot-password/send", methods=["POST"])
@limiter.limit("5 per minute; 20 per hour")
def send_forgot_password_otp():
    data = request.get_json(silent=True) or request.form
    email = sanitize_text(data.get("email") or "", max_length=120).lower()

    if not email or "@" not in email or "." not in email:
        return jsonify({"success": False, "message": "Please enter a valid email address."}), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        user = supabase_get_user_by_email(email)
    if not user:
        return jsonify({"success": False, "message": "No account found with that email address. Please check your email or sign up."}), 404

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=30)).isoformat()
    now_iso = now.isoformat()

    try:
        db.execute("DELETE FROM email_otps WHERE email = ? AND expires_at < ?", (email, now_iso))
        db.execute(
            "INSERT INTO email_otps (email, otp_code, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (email, otp_code, expires_at, now_iso),
        )
        db.commit()
        supabase_save_otp(email, otp_code, expires_at, now_iso)
    except Exception as exc:
        return jsonify({"success": False, "message": f"Database error: {exc}"}), 500

    sent, status_or_msg = send_password_reset_email(email, otp_code)
    if sent:
        return jsonify({
            "success": True,
            "message": f"Password reset verification code sent to {email}. Please check your inbox.",
        })
    else:
        return jsonify({
            "success": False,
            "message": _format_email_error(status_or_msg),
        }), 400


@auth_bp.route("/forgot-password/reset", methods=["POST"])
@auth_bp.route("/auth/forgot-password/reset", methods=["POST"])
@limiter.limit("10 per minute; 40 per hour")
def reset_forgot_password():
    data = request.get_json(silent=True) or request.form
    email = sanitize_text(data.get("email") or "", max_length=120).lower()
    otp_code = (data.get("otp") or "").strip()
    new_password = (data.get("password") or "").strip()

    if not email or not otp_code or not new_password:
        return jsonify({"success": False, "message": "Email, verification code, and new password are required."}), 400

    is_valid_pwd, pwd_err = validate_password_strength(new_password)
    if not is_valid_pwd:
        return jsonify({"success": False, "message": pwd_err}), 400

    now_iso = datetime.now(timezone.utc).isoformat()
    db = get_db()
    record = db.execute(
        "SELECT * FROM email_otps WHERE email = ? AND otp_code = ? AND expires_at >= ?",
        (email, otp_code, now_iso),
    ).fetchone()

    sb_valid = False
    if not record:
        sb_valid = supabase_verify_otp(email, otp_code)

    if not record and not sb_valid:
        return jsonify({
            "success": False,
            "message": "Invalid or expired verification code. Please check the code or request a new one.",
        }), 400

    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        user = supabase_get_user_by_email(email)
    if not user:
        return jsonify({"success": False, "message": "User account not found."}), 404

    pwd_hash = generate_password_hash(new_password)
    db.execute("UPDATE users SET password_hash = ? WHERE email = ?", (pwd_hash, email))
    db.execute("DELETE FROM email_otps WHERE email = ?", (email,))
    db.commit()
    supabase_update_password(email, pwd_hash)
    supabase_delete_otps(email)

    session.permanent = True
    session["user_id"] = user["id"]
    session["user"] = user["name"]

    resp = jsonify({
        "success": True,
        "redirect_url": url_for("dashboard"),
        "message": "Password updated successfully! Logging you in...",
    })
    resp.set_cookie("remember_email", email, max_age=30 * 86400, samesite="Lax")
    return resp


@auth_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

