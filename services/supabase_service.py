"""
Supabase client helper for CareerForge AI.
Supports both public (anon) client and privileged (service_role) admin client.
"""
import logging
from typing import Optional
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


def get_supabase_client() -> Optional["Client"]:
    """
    Returns the Supabase client initialized with the anonymous (public) key.
    This client is subject to Row Level Security (RLS) policies.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_INSTALLED:
        logger.warning("[Supabase] supabase-py package is not installed.")
        return None

    url = Config.SUPABASE_URL
    key = Config.SUPABASE_ANON_KEY or Config.SUPABASE_PUBLIC_KEY

    if not url or not key or "your-project-id" in url or "your-anon" in key:
        logger.debug("[Supabase] SUPABASE_URL or SUPABASE_ANON_KEY not configured in .env.")
        return None

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

    if not SUPABASE_INSTALLED:
        logger.warning("[Supabase] supabase-py package is not installed.")
        return None

    url = Config.SUPABASE_URL
    key = Config.SUPABASE_SERVICE_ROLE_KEY or Config.SUPABASE_ANON_KEY or Config.SUPABASE_PUBLIC_KEY

    if not url or not key or "your-project-id" in url or "your-service-role" in key:
        logger.debug("[Supabase] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not configured in .env.")
        return None

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
    url = Config.SUPABASE_URL
    anon_key = Config.SUPABASE_ANON_KEY or Config.SUPABASE_PUBLIC_KEY
    service_role_key = Config.SUPABASE_SERVICE_ROLE_KEY

    is_placeholder_url = not url or "your-project-id" in url
    is_placeholder_anon = not anon_key or "your-anon" in anon_key
    is_placeholder_service = not service_role_key or "your-service-role" in service_role_key

    client = get_supabase_client()
    admin_client = get_supabase_admin_client()

    return {
        "installed": SUPABASE_INSTALLED,
        "configured": bool(not is_placeholder_url and (not is_placeholder_anon or not is_placeholder_service)),
        "url": url if not is_placeholder_url else None,
        "has_anon_key": bool(anon_key and not is_placeholder_anon),
        "has_public_key": bool(anon_key and not is_placeholder_anon),
        "has_service_role_key": bool(service_role_key and not is_placeholder_service),
        "client_ready": client is not None,
        "admin_client_ready": admin_client is not None,
    }
