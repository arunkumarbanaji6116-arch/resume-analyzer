from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db

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


@auth_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))
