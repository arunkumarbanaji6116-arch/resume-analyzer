import sqlite3

from flask import Flask, flash, g, redirect, render_template, request, session
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(Config.DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    db = sqlite3.connect(Config.DATABASE)
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
        """
    )
    db.commit()
    db.close()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    Config.DATABASE.parent.mkdir(parents=True, exist_ok=True)
    init_db()

    @app.teardown_appcontext
    def close_db(_error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_upload(_error):
        flash("Resume images must be 8 MB or smaller.")
        return redirect(request.url)

    @app.context_processor
    def inject_user():
        return {"current_user": session.get("user")}

    @app.get("/")
    def landing():
        return render_template("landing.html")

    @app.get("/dashboard")
    def dashboard():
        if "user_id" not in session:
            return render_template("landing.html")
        rows = get_db().execute(
            "SELECT kind, title, score, created_at FROM activity WHERE user_id = ? ORDER BY id DESC LIMIT 6",
            (session["user_id"],),
        ).fetchall()
        return render_template("dashboard.html", activities=rows)

    from routes.auth import auth_bp
    from routes.resume import resume_bp
    from routes.interview import interview_bp
    from routes.career import career_bp
    from routes.jobs import jobs_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(career_bp)
    app.register_blueprint(jobs_bp)
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
