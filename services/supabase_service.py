"""
Supabase client helper and database sync service for CareerForge AI.
Supports both public (anon) client and privileged (service_role) admin client.
Provides automatic synchronization between local storage and Supabase.
"""
from datetime import datetime, timezone
import logging
from typing import Optional, List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
    SUPABASE_INSTALLED = True
except ImportError:
    SUPABASE_INSTALLED = False
    Client = None

_supabase_client: Optional["Client"] = None
_supabase_admin_client: Optional["Client"] = None


def is_supabase_configured() -> bool:
    """Returns True if valid non-placeholder Supabase credentials are set."""
    url = Config.SUPABASE_URL
    key = Config.SUPABASE_SERVICE_ROLE_KEY or Config.SUPABASE_ANON_KEY or Config.SUPABASE_PUBLIC_KEY
    if not url or not key:
        return False
    if "your-project-id" in url or "your-anon" in key or "your-service-role" in key:
        return False
    return True


def get_supabase_client() -> Optional["Client"]:
    """
    Returns the Supabase client initialized with the anonymous (public) key.
    This client is subject to Row Level Security (RLS) policies.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_INSTALLED or not is_supabase_configured():
        return None

    url = Config.SUPABASE_URL
    key = Config.SUPABASE_ANON_KEY or Config.SUPABASE_PUBLIC_KEY or Config.SUPABASE_SERVICE_ROLE_KEY

    try:
        _supabase_client = create_client(url, key)
        logger.info("[Supabase] Client initialized successfully with Anon/Public key.")
        return _supabase_client
    except Exception as exc:
        logger.error(f"[Supabase] Error initializing client: {exc}")
        return None


def get_supabase_admin_client() -> Optional["Client"]:
    """
    Returns the Supabase client initialized with the service_role key.
    WARNING: The service_role key bypasses Row Level Security (RLS).
    Use only for server-side administrative tasks, migrations, or privileged data operations.
    """
    global _supabase_admin_client
    if _supabase_admin_client is not None:
        return _supabase_admin_client

    if not SUPABASE_INSTALLED or not is_supabase_configured():
        return None

    url = Config.SUPABASE_URL
    key = Config.SUPABASE_SERVICE_ROLE_KEY or Config.SUPABASE_ANON_KEY or Config.SUPABASE_PUBLIC_KEY

    try:
        _supabase_admin_client = create_client(url, key)
        logger.info("[Supabase] Admin client initialized successfully with Service Role key.")
        return _supabase_admin_client
    except Exception as exc:
        logger.error(f"[Supabase] Error initializing admin client: {exc}")
        return None


def check_supabase_connection() -> dict:
    """
    Check the current configuration and connection status of Supabase.
    Returns status dictionary with configuration flags and ready state.
    """
    configured = is_supabase_configured()
    client = get_supabase_client() if configured else None
    admin_client = get_supabase_admin_client() if configured else None

    anon_key = Config.SUPABASE_ANON_KEY or Config.SUPABASE_PUBLIC_KEY
    service_role_key = Config.SUPABASE_SERVICE_ROLE_KEY

    return {
        "installed": SUPABASE_INSTALLED,
        "configured": configured,
        "url": Config.SUPABASE_URL if configured else None,
        "has_anon_key": bool(anon_key and "your-anon" not in anon_key),
        "has_public_key": bool(anon_key and "your-anon" not in anon_key),
        "has_service_role_key": bool(service_role_key and "your-service-role" not in service_role_key),
        "client_ready": client is not None,
        "admin_client_ready": admin_client is not None,
    }


# ==============================================================================
# Supabase User Operations
# ==============================================================================

def supabase_get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve a user record from Supabase by email."""
    client = get_supabase_admin_client() or get_supabase_client()
    if not client:
        return None
    try:
        clean_email = email.strip().lower()
        res = client.table("users").select("*").eq("email", clean_email).limit(1).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as exc:
        logger.debug(f"[Supabase] get_user_by_email error: {exc}")
        return None


def supabase_create_user(name: str, email: str, password_hash: str, created_at: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Create or update a user record in Supabase."""
    client = get_supabase_admin_client() or get_supabase_client()
    if not client:
        return None
    now_iso = created_at or datetime.now(timezone.utc).isoformat()
    record = {
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": password_hash,
        "created_at": now_iso,
    }
    try:
        res = client.table("users").upsert(record, on_conflict="email").execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return record
    except Exception as exc:
        logger.debug(f"[Supabase] create_user error: {exc}")
        return None


def supabase_update_password(email: str, password_hash: str) -> bool:
    """Update a user's password hash in Supabase."""
    client = get_supabase_admin_client() or get_supabase_client()
    if not client:
        return False
    try:
        clean_email = email.strip().lower()
        res = client.table("users").update({"password_hash": password_hash}).eq("email", clean_email).execute()
        return bool(res.data)
    except Exception as exc:
        logger.debug(f"[Supabase] update_password error: {exc}")
        return False


# ==============================================================================
# Supabase OTP Operations
# ==============================================================================

def supabase_save_otp(email: str, otp_code: str, expires_at: str, created_at: Optional[str] = None) -> bool:
    """Store an OTP in Supabase email_otps table and clean up expired codes."""
    client = get_supabase_admin_client() or get_supabase_client()
    if not client:
        return False
    now_iso = created_at or datetime.now(timezone.utc).isoformat()
    clean_email = email.strip().lower()
    try:
        # Delete expired OTPs for this email
        client.table("email_otps").delete().eq("email", clean_email).lt("expires_at", now_iso).execute()
        # Insert new OTP
        res = client.table("email_otps").insert({
            "email": clean_email,
            "otp_code": str(otp_code).strip(),
            "expires_at": expires_at,
            "created_at": now_iso,
        }).execute()
        return bool(res.data)
    except Exception as exc:
        logger.debug(f"[Supabase] save_otp error: {exc}")
        return False


def supabase_verify_otp(email: str, otp_code: str) -> bool:
    """Verify if a valid, non-expired OTP exists in Supabase."""
    client = get_supabase_admin_client() or get_supabase_client()
    if not client:
        return False
    now_iso = datetime.now(timezone.utc).isoformat()
    clean_email = email.strip().lower()
    try:
        res = (
            client.table("email_otps")
            .select("*")
            .eq("email", clean_email)
            .eq("otp_code", str(otp_code).strip())
            .gte("expires_at", now_iso)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return bool(res.data and len(res.data) > 0)
    except Exception as exc:
        logger.debug(f"[Supabase] verify_otp error: {exc}")
        return False


def supabase_delete_otps(email: str) -> bool:
    """Delete all OTP records for an email from Supabase."""
    client = get_supabase_admin_client() or get_supabase_client()
    if not client:
        return False
    try:
        client.table("email_otps").delete().eq("email", email.strip().lower()).execute()
        return True
    except Exception as exc:
        logger.debug(f"[Supabase] delete_otps error: {exc}")
        return False


# ==============================================================================
# Supabase Activity Operations
# ==============================================================================

def supabase_save_activity(user_id: int, kind: str, title: str, score: Optional[int] = None, created_at: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Log an activity record to Supabase."""
    client = get_supabase_admin_client() or get_supabase_client()
    if not client:
        return None
    now_iso = created_at or datetime.now(timezone.utc).isoformat()
    try:
        res = client.table("activity").insert({
            "user_id": user_id,
            "kind": kind,
            "title": title,
            "score": score,
            "created_at": now_iso,
        }).execute()
        return res.data[0] if res.data else None
    except Exception as exc:
        logger.debug(f"[Supabase] save_activity error: {exc}")
        return None


def supabase_get_activities(user_id: int, limit: int = 6) -> List[Dict[str, Any]]:
    """Retrieve user activities from Supabase."""
    client = get_supabase_admin_client() or get_supabase_client()
    if not client:
        return []
    try:
        res = (
            client.table("activity")
            .select("kind, title, score, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception as exc:
        logger.debug(f"[Supabase] get_activities error: {exc}")
        return []


# ==============================================================================
# Sync & Migration Utility
# ==============================================================================

def migrate_local_db_to_supabase() -> dict:
    """
    Synchronizes existing SQLite users and activity into Supabase.
    Safe to run repeatedly; uses upsert on unique keys.
    """
    import sqlite3

    if not is_supabase_configured():
        return {"status": "skipped", "reason": "Supabase not configured"}

    client = get_supabase_admin_client() or get_supabase_client()
    if not client:
        return {"status": "skipped", "reason": "Supabase client unavailable"}

    if not Config.DATABASE.exists():
        return {"status": "skipped", "reason": "Local database does not exist"}

    synced_users = 0
    synced_activities = 0

    try:
        conn = sqlite3.connect(Config.DATABASE)
        conn.row_factory = sqlite3.Row

        # 1. Sync users
        users = conn.execute("SELECT id, name, email, password_hash, created_at FROM users").fetchall()
        for u in users:
            try:
                res = client.table("users").upsert({
                    "id": u["id"],
                    "name": u["name"],
                    "email": u["email"],
                    "password_hash": u["password_hash"],
                    "created_at": u["created_at"],
                }, on_conflict="email").execute()
                if res.data:
                    synced_users += 1
            except Exception as e:
                logger.debug(f"[Supabase] User sync row error: {e}")

        # 2. Sync activity
        activities = conn.execute("SELECT user_id, kind, title, score, created_at FROM activity").fetchall()
        for a in activities:
            try:
                client.table("activity").insert({
                    "user_id": a["user_id"],
                    "kind": a["kind"],
                    "title": a["title"],
                    "score": a["score"],
                    "created_at": a["created_at"],
                }).execute()
                synced_activities += 1
            except Exception as e:
                logger.debug(f"[Supabase] Activity sync row error: {e}")

        conn.close()
        return {
            "status": "success",
            "synced_users": synced_users,
            "synced_activities": synced_activities,
        }
    except Exception as exc:
        logger.debug(f"[Supabase] Migration error: {exc}")
        return {"status": "error", "error": str(exc)}
