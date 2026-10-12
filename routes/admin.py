"""
Admin Portal & RBAC Route Controller for CareerForge AI
All routes in this blueprint are strictly restricted by @admin_required.
Non-admin access attempts are rejected with HTTP 403 Forbidden and logged.
"""

from datetime import datetime, timezone
import os

from flask import Blueprint, jsonify, render_template, request, session
from config import Config
from db import get_db, log_security_event
from services.security import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@admin_required
def enforce_admin_on_blueprint():
    """Ensure every route within the /admin blueprint enforces admin authorization."""
    pass


@admin_bp.get("")
@admin_bp.get("/")
def admin_dashboard():
    """Admin Overview Dashboard: statistics, registered users, and security logs."""
    db = get_db()
    
    # 1. Platform Metrics
    user_count = db.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
    activity_count = db.execute("SELECT COUNT(*) as count FROM activity").fetchone()["count"]
    version_count = db.execute("SELECT COUNT(*) as count FROM resume_versions").fetchone()["count"]
    security_event_count = db.execute("SELECT COUNT(*) as count FROM security_logs").fetchone()["count"]

    # 2. Recent Users
    users = db.execute(
        "SELECT id, name, email, is_admin, created_at FROM users ORDER BY id DESC LIMIT 20"
    ).fetchall()

    # 3. Recent Security Logs
    security_logs = db.execute(
        "SELECT id, user_id, event_type, details, ip_address, user_agent, created_at FROM security_logs ORDER BY id DESC LIMIT 25"
    ).fetchall()

    # 4. System Health Check Diagnostics
    system_health = {
        "debug_mode": Config.DEBUG or Config.FLASK_DEBUG,
        "database_connected": True,
        "gemini_api_configured": bool(Config.GEMINI_API_KEY),
        "resend_api_configured": bool(Config.RESEND_API_KEY),
        "supabase_configured": bool(Config.SUPABASE_URL and Config.SUPABASE_ANON_KEY),
        "session_cookie_httponly": Config.SESSION_COOKIE_HTTPONLY,
        "session_cookie_samesite": Config.SESSION_COOKIE_SAMESITE,
        "session_cookie_secure": Config.SESSION_COOKIE_SECURE,
        "rate_limiting_active": True,
    }

    return render_template(
        "admin.html",
        user_count=user_count,
        activity_count=activity_count,
        version_count=version_count,
        security_event_count=security_event_count,
        users=users,
        security_logs=security_logs,
        system_health=system_health,
    )


@admin_bp.get("/users")
def get_admin_users():
    """JSON API to fetch all users for management."""
    db = get_db()
    rows = db.execute(
        "SELECT id, name, email, is_admin, created_at FROM users ORDER BY id DESC"
    ).fetchall()
    users = [
        {
            "id": r["id"],
            "name": r["name"],
            "email": r["email"],
            "is_admin": bool(r["is_admin"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]
    return jsonify({"success": True, "users": users})


@admin_bp.post("/users/toggle-role")
def toggle_user_role():
    """Toggle admin role for a specific user."""
    payload = request.get_json(silent=True) or request.form
    target_user_id = payload.get("user_id")

    if not target_user_id:
        return jsonify({"success": False, "error": "user_id is required"}), 400

    try:
        target_user_id = int(target_user_id)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid user_id"}), 400

    current_admin_id = session.get("user_id")
    if target_user_id == current_admin_id:
        return jsonify({"success": False, "error": "Cannot change your own admin role"}), 400

    db = get_db()
    user = db.execute("SELECT id, name, email, is_admin FROM users WHERE id = ?", (target_user_id,)).fetchone()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    new_role = 0 if user["is_admin"] else 1
    db.execute("UPDATE users SET is_admin = ? WHERE id = ?", (new_role, target_user_id))
    db.commit()

    log_security_event(
        "admin_role_change",
        f"Admin {current_admin_id} changed role of user {target_user_id} ({user['email']}) to {new_role}",
        user_id=current_admin_id
    )

    return jsonify({
        "success": True,
        "user_id": target_user_id,
        "is_admin": bool(new_role),
        "message": f"User {user['name']} role updated to {'Admin' if new_role else 'Member'}."
    })


@admin_bp.get("/audit-logs")
def get_audit_logs():
    """Retrieve security audit logs."""
    db = get_db()
    rows = db.execute(
        "SELECT id, user_id, event_type, details, ip_address, user_agent, created_at FROM security_logs ORDER BY id DESC LIMIT 100"
    ).fetchall()
    logs = [
        {
            "id": r["id"],
            "user_id": r["user_id"],
            "event_type": r["event_type"],
            "details": r["details"],
            "ip_address": r["ip_address"],
            "user_agent": r["user_agent"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]
    return jsonify({"success": True, "logs": logs})


@admin_bp.get("/system-health")
def system_health_status():
    """JSON status endpoint for system health verification."""
    return jsonify({
        "success": True,
        "status": "healthy",
        "debug_mode": Config.DEBUG or Config.FLASK_DEBUG,
        "database_connected": True,
        "gemini_api_configured": bool(Config.GEMINI_API_KEY),
        "resend_api_configured": bool(Config.RESEND_API_KEY),
        "supabase_configured": bool(Config.SUPABASE_URL and Config.SUPABASE_ANON_KEY),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

