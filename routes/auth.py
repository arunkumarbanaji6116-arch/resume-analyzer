from datetime import datetime, timedelta, timezone
import re
import secrets

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db
from services.smtp_service import is_smtp_configured, send_otp_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session["user_id"] = user["id"]
            session["user"] = user["name"]
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")


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
        session["user_id"] = cursor.lastrowid
        session["user"] = name
        return redirect(url_for("dashboard"))
    except Exception:
        flash("An account with that email already exists.", "error")
        return redirect(url_for("auth.login", mode="signup"))


@auth_bp.route("/google-otp/send", methods=["POST"])
@auth_bp.route("/auth/google-otp/send", methods=["POST"])
def send_google_otp():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()

    if not email or "@" not in email or "." not in email:
        return jsonify({"success": False, "message": "Please enter a valid Google email address."}), 400

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=10)).isoformat()

    try:
        db = get_db()
        db.execute("DELETE FROM email_otps WHERE email = ?", (email,))
        db.execute(
            "INSERT INTO email_otps (email, otp_code, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (email, otp_code, expires_at, now.isoformat()),
        )
        db.commit()
    except Exception as exc:
        return jsonify({"success": False, "message": f"Database error storing OTP: {exc}"}), 500

    session["google_auth_email"] = email

    sent, status_or_msg = send_otp_email(email, otp_code)

    if status_or_msg == "dev_mode":
        return jsonify({
            "success": True,
            "is_dev_mode": True,
            "dev_code": otp_code,
            "message": f"Email service not configured in .env. Test PIN is: {otp_code}",
        })
    elif sent:
        return jsonify({
            "success": True,
            "is_dev_mode": False,
            "message": f"Verification code successfully sent to {email}. Please check your inbox.",
        })
    else:
        return jsonify({
            "success": True,
            "is_dev_mode": True,
            "dev_code": otp_code,
            "message": f"Email delivery failed ({status_or_msg}). For testing, your PIN is: {otp_code}",
        })


@auth_bp.route("/google-otp/verify", methods=["POST"])
@auth_bp.route("/auth/google-otp/verify", methods=["POST"])
def verify_google_otp():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or session.get("google_auth_email") or "").strip().lower()
    otp_code = (data.get("otp") or "").strip()

    if not email or not otp_code:
        return jsonify({"success": False, "message": "Email and verification code are required."}), 400

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

    session["user_id"] = user_id
    session["user"] = user_name
    session.pop("google_auth_email", None)

    return jsonify({
        "success": True,
        "redirect_url": url_for("dashboard"),
        "user_name": user_name,
    })


@auth_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

