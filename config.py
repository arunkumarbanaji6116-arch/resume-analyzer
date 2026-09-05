from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-before-production")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("SECRET_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    DATABASE = BASE_DIR / "database" / "careerforge.db"
    GENERATED_DIR = BASE_DIR / "generated" / "resumes"
    # Resume screenshots are processed in memory and are never saved by the app.
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
