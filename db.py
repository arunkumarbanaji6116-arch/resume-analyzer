from datetime import datetime, timezone
import os
import sqlite3
import threading

from flask import g, request
from config import Config


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(Config.DATABASE, timeout=10)
        g.db.row_factory = sqlite3.Row
        try:
            g.db.execute("PRAGMA journal_mode = WAL;")
            g.db.execute("PRAGMA synchronous = NORMAL;")
            g.db.execute("PRAGMA cache_size = -64000;")
            g.db.execute("PRAGMA temp_store = MEMORY;")
        except Exception:
            pass
    return g.db


def init_db():
    Config.DATABASE.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(Config.DATABASE, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA journal_mode = WAL;")
        db.execute("PRAGMA synchronous = NORMAL;")
    except Exception:
        pass
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            score INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS email_otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS resume_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            version_name TEXT NOT NULL,
            target_role TEXT,
            ats_score INTEGER,
            strategy TEXT,
            resume_data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL
        );
        """
    )

    # Automatic schema migration: ensure is_admin column exists if table pre-existed
    try:
        cols = [row[1] for row in db.execute("PRAGMA table_info(users);").fetchall()]
        if "is_admin" not in cols:
            db.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0;")
            db.commit()
    except Exception:
        pass

    # Admin seeding: automatically grant admin status to configured admin email if present
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    if admin_email:
        try:
            db.execute("UPDATE users SET is_admin = 1 WHERE lower(email) = ?", (admin_email,))
            db.commit()
        except Exception:
            pass

    db.commit()
    db.close()

    # Attempt automatic synchronization to Supabase if credentials are provided
    try:
        from services.supabase_service import is_supabase_configured, migrate_local_db_to_supabase
        if is_supabase_configured():
            migrate_local_db_to_supabase()
    except Exception:
        pass


def record_activity(user_id, kind, title, score=None, created_at=None):
    """
    Records an activity locally in SQLite and synchronizes to Supabase (if configured).
    """
    now_iso = created_at or datetime.now(timezone.utc).isoformat()

    # 1. Local SQLite record
    try:
        db = get_db()
        db.execute(
            "INSERT INTO activity (user_id, kind, title, score, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, kind, title, score, now_iso),
        )
        db.commit()
    except Exception:
        pass

    # 2. Supabase Cloud Sync (Executed asynchronously in background thread for 0ms delay)
    try:
        def _bg_supabase_sync():
            try:
                from services.supabase_service import supabase_save_activity
                supabase_save_activity(user_id, kind, title, score, now_iso)
            except Exception:
                pass
        threading.Thread(target=_bg_supabase_sync, daemon=True).start()
    except Exception:
        pass


def log_security_event(event_type: str, details: str = "", user_id: int | None = None):
    """
    Records a defensive security audit log event with IP address, user agent, and timestamp.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    ip_addr = "127.0.0.1"
    user_agent = "system"

    try:
        if request:
            ip_addr = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
            user_agent = request.headers.get("User-Agent", "unknown")[:255]
    except Exception:
        pass

    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO security_logs (user_id, event_type, details, ip_address, user_agent, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, event_type, details[:500] if details else None, ip_addr, user_agent, now_iso)
        )
        db.commit()
    except Exception:
        pass
