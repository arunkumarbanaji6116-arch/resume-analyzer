import sqlite3
from flask import g
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
        """
    )
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
    from datetime import datetime, timezone
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

    # 2. Supabase Cloud Sync
    try:
        from services.supabase_service import supabase_save_activity
        supabase_save_activity(user_id, kind, title, score, now_iso)
    except Exception:
        pass

