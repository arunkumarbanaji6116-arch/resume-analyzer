from pathlib import Path
import os
import tempfile

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "careerforge-session-secret-2026")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("SECRET_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    if IS_VERCEL:
        _tmp = Path(tempfile.gettempdir())
        DATABASE = _tmp / "careerforge.db"
        GENERATED_DIR = _tmp / "resumes"
    else:
        DATABASE = BASE_DIR / "database" / "careerforge.db"
        GENERATED_DIR = BASE_DIR / "generated" / "resumes"

    # Resume screenshots are processed in memory and are never saved by the app.
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
