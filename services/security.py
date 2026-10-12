"""
Security & Defensive Hardening Module for CareerForge AI
Provides input sanitization, access control decorators, password strength validation,
safe redirect checks, and security event audit logging.
"""

from functools import wraps
import logging
import re
from urllib.parse import urljoin, urlparse

from flask import abort, flash, jsonify, redirect, request, session, url_for
import bleach

logger = logging.getLogger("security")


def sanitize_text(text: str | None, max_length: int = 15000) -> str:
    """
    Sanitizes user-supplied string against XSS, null bytes, and malicious HTML/scripts.
    Strips all HTML tags and enforces bounded maximum string length.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # 1. Strip null bytes and control chars (except normal whitespace: newline, tab, cr)
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

    # 2. Bleach HTML tag stripping (zero tags or attributes allowed)
    cleaned = bleach.clean(cleaned, tags=[], attributes={}, strip=True)

    # 3. Enforce maximum length to prevent resource exhaustion / buffer overflow DoS
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned.strip()


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validates that a password satisfies essential security criteria:
    - At least 8 characters
    - Not entirely numeric
    - Not entirely whitespace
    - Maximum 128 characters to prevent bcrypt/scrypt DoS
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
    if password.strip() == "":
        return False, "Password cannot be entirely whitespace."
    if password.isdigit():
        return False, "Password must include letters or symbols, not only digits."
    return True, ""


def is_safe_url(target: str) -> bool:
    """
    Verifies that a redirect target URL is safe and relative to this origin,
    preventing Open Redirect vulnerabilities (CWE-601).
    """
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def is_authenticated() -> bool:
    """Checks whether the current request session contains a valid user ID."""
    return bool(session.get("user_id"))


def is_admin_user() -> bool:
    """
    Verifies against the database whether the current authenticated user has administrator privileges.
    """
    user_id = session.get("user_id")
    if not user_id:
        return False

    # Check cached session flag if present
    if session.get("is_admin") is True:
        return True

    try:
        from db import get_db
        db = get_db()
        row = db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
        if row and bool(row["is_admin"]):
            session["is_admin"] = True
            return True
    except Exception as exc:
        logger.error(f"Error checking admin status for user {user_id}: {exc}")

    return False


def login_required(f):
    """
    Decorator that requires user authentication.
    Returns JSON 401 for AJAX/API requests and redirects to login for standard page requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            is_api = (
                request.headers.get("X-Requested-With") == "XMLHttpRequest"
                or request.is_json
                or "application/json" in request.headers.get("Accept", "")
                or request.path.startswith("/api/")
                or (request.method == "POST" and not request.form.get("csrf_form_submit"))
            )
            # If it's a browser page GET navigation, redirect to login
            if request.method == "GET" and not request.is_json and "text/html" in request.headers.get("Accept", ""):
                next_url = request.full_path if is_safe_url(request.full_path) else None
                return redirect(url_for("auth.login", next=next_url))

            if is_api:
                return jsonify({
                    "success": False,
                    "error": "Unauthorized",
                    "message": "Authentication required. Please sign in to continue."
                }), 401

            next_url = request.full_path if is_safe_url(request.full_path) else None
            return redirect(url_for("auth.login", next=next_url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator that strictly requires administrator authorization (RBAC).
    Logs unauthorized access attempts and returns 403 Forbidden.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                return jsonify({
                    "success": False,
                    "error": "Unauthorized",
                    "message": "Authentication required."
                }), 401
            return redirect(url_for("auth.login", next=request.full_path if is_safe_url(request.full_path) else None))

        if not is_admin_user():
            user_id = session.get("user_id")
            client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
            logger.warning(
                f"[SECURITY ALERT] Unauthorized admin access attempt by user_id={user_id} "
                f"from ip={client_ip} on path={request.path}"
            )
            try:
                from db import log_security_event
                log_security_event("unauthorized_admin_access", f"Attempted path: {request.path}", user_id=user_id)
            except Exception:
                pass

            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                return jsonify({
                    "success": False,
                    "error": "Forbidden",
                    "message": "Access denied. Administrator privileges required."
                }), 403

            abort(403)

        return f(*args, **kwargs)
    return decorated_function
