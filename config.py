from pathlib import Path
import os
import tempfile

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "careerforge-session-secret-2026")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("SECRET_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_DEFAULT_VOICE = os.getenv("ELEVENLABS_DEFAULT_VOICE", "21m00Tcm4TlvDq8ikWAM")

    # Resend API Configuration (https://resend.com)
    RESEND_API_KEY = (
        os.getenv("RESEND_API_KEY", "").strip()
        or os.getenv("RESEND_KEY", "").strip()
        or os.getenv("RESEND_API", "").strip()
    )
    RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "CareerForge.AI <onboarding@resend.dev>").strip()

    # SMTP Configuration (fallback or custom SMTP)
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").strip().lower() in ("true", "1", "yes")
    SMTP_USER = os.getenv("SMTP_USER", "").strip()
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip() or os.getenv("SMTP_USER", "").strip() or "noreply@careerforge.ai"
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "CareerForge.AI").strip()

    if IS_VERCEL:
        _tmp = Path(tempfile.gettempdir())
        DATABASE = _tmp / "careerforge.db"
        GENERATED_DIR = _tmp / "resumes"
    else:
        DATABASE = BASE_DIR / "database" / "careerforge.db"
        GENERATED_DIR = BASE_DIR / "generated" / "resumes"

    # Resume screenshots are processed in memory and are never saved by the app.
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
