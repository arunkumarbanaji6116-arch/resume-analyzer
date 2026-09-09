from datetime import datetime, timedelta, timezone
import logging
import os
import re
import secrets

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
import requests
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db
from services.smtp_service import (
    is_smtp_configured,
    send_github_otp_email,
    send_otp_email,
    send_password_reset_email,
)

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.permanent = bool(remember)
            session["user_id"] = user["id"]
            session["user"] = user["name"]
            resp = redirect(url_for("dashboard"))
            if remember:
                resp.set_cookie("remember_email", email, max_age=30 * 86400, samesite="Lax")
            else:
                resp.delete_cookie("remember_email")
            return resp

        # Helpful hint if user exists but has google auth
        if user and user["password_hash"] == "google_smtp_verified":
            flash("This account was created with Google Sign-In. Click 'Google' below to log in or reset your password.", "error")
        else:
            flash("Email or password is incorrect.", "error")

        return render_template("login.html", email=email, password=password if remember else "", remember=remember)

    remember_email = request.cookies.get("remember_email", "")
    return render_template("login.html", email=remember_email, remember=bool(remember_email))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return redirect(url_for("auth.login", mode="signup"))
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not name or not email or len(password) < 8:
        flash("Enter a name, a valid email, and a password of at least 8 characters.", "error")
        return redirect(url_for("auth.login", mode="signup"))
    try:
        db = get_db()
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, generate_password_hash(password), datetime.now(timezone.utc).isoformat()),
        )
        db.commit()
        session.permanent = True
        session["user_id"] = cursor.lastrowid
        session["user"] = name
        resp = redirect(url_for("dashboard"))
        resp.set_cookie("remember_email", email, max_age=30 * 86400, samesite="Lax")
        return resp
    except Exception:
        flash("An account with that email already exists.", "error")
        return redirect(url_for("auth.login", mode="signup"))


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
def send_google_otp():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()

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
def verify_google_otp():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or session.get("google_auth_email") or "").strip().lower()
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

    if not record:
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

    # Verification successful: clear all OTPs for this email
    db.execute("DELETE FROM email_otps WHERE email = ?", (email,))
    db.commit()

    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
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
def send_github_otp():
    data = request.get_json(silent=True) or request.form
    raw_input = (data.get("identifier") or data.get("email") or "").strip()

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
def verify_github_otp():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or session.get("github_auth_email") or "").strip().lower()
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

    if not record:
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

    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
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
def send_forgot_password_otp():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()

    if not email or "@" not in email or "." not in email:
        return jsonify({"success": False, "message": "Please enter a valid email address."}), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
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
def reset_forgot_password():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()
    otp_code = (data.get("otp") or "").strip()
    new_password = (data.get("password") or "").strip()

    if not email or not otp_code or not new_password:
        return jsonify({"success": False, "message": "Email, verification code, and new password are required."}), 400

    if len(new_password) < 8:
        return jsonify({"success": False, "message": "New password must be at least 8 characters long."}), 400

    now_iso = datetime.now(timezone.utc).isoformat()
    db = get_db()
    record = db.execute(
        "SELECT * FROM email_otps WHERE email = ? AND otp_code = ? AND expires_at >= ?",
        (email, otp_code, now_iso),
    ).fetchone()

    if not record:
        return jsonify({
            "success": False,
            "message": "Invalid or expired verification code. Please check the code or request a new one.",
        }), 400

    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        return jsonify({"success": False, "message": "User account not found."}), 404

    db.execute("UPDATE users SET password_hash = ? WHERE email = ?", (generate_password_hash(new_password), email))
    db.execute("DELETE FROM email_otps WHERE email = ?", (email,))
    db.commit()

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

