from datetime import timedelta
from pathlib import Path
import os
import secrets
import tempfile

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class Config:
    # 1. Secret Key Management (Defensive Isolation)
    _raw_secret = os.getenv("SECRET_KEY", "").strip()
    if not _raw_secret or _raw_secret == "change-this-before-production":
        SECRET_KEY = os.getenv("CAREERFORGE_STATIC_SECRET", "careerforge-session-sec-v2026-9f8a3b2c1d")
    else:
        SECRET_KEY = _raw_secret

    # 2. Strict Session Cookie Hardening (OWASP ASVS Standard)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in ("true", "1")
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)

    # 3. Environment & Debug Controls (Strictly Disabled by Default)
    DEBUG = False
    TESTING = False
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1")

    # 4. API Keys & AI Providers (Never Fallback to Session Secret Key)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
    ELEVENLABS_DEFAULT_VOICE = os.getenv("ELEVENLABS_DEFAULT_VOICE", "21m00Tcm4TlvDq8ikWAM")

    # 5. Rate Limiting Defaults
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_DEFAULT = "300 per minute; 3000 per hour"

    # 6. CORS Settings
    ALLOWED_ORIGINS = [
        o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()
    ] or ["http://localhost:5000", "http://127.0.0.1:5000", "https://mycareerforge.in"]

    # 7. Resend API Configuration (https://resend.com)
    RESEND_API_KEY = (
        os.getenv("RESEND_API_KEY", "").strip()
        or os.getenv("RESEND_KEY", "").strip()
        or os.getenv("RESEND_API", "").strip()
    )
    RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "CareerForge.AI <auth@mycareerforge.in>").strip()

    # 8. SMTP Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").strip().lower() in ("true", "1", "yes")
    SMTP_USER = os.getenv("SMTP_USER", "").strip()
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip() or os.getenv("SMTP_USER", "").strip() or "noreply@careerforge.ai"
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "CareerForge.AI").strip()

    # 9. Supabase Configuration (https://supabase.com)
    SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
    SUPABASE_ANON_KEY = (
        os.getenv("SUPABASE_ANON_KEY", "").strip()
        or os.getenv("SUPABASE_PUBLIC_KEY", "").strip()
    )
    SUPABASE_PUBLIC_KEY = (
        os.getenv("SUPABASE_PUBLIC_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    # 10. Database & Storage Paths
    if IS_VERCEL:
        _tmp = Path(tempfile.gettempdir())
        DATABASE = _tmp / "careerforge.db"
        GENERATED_DIR = _tmp / "resumes"
    else:
        DATABASE = BASE_DIR / "database" / "careerforge.db"
        GENERATED_DIR = BASE_DIR / "generated" / "resumes"

    # 11. Bounded Upload Bounds (8 MB max payload)
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
