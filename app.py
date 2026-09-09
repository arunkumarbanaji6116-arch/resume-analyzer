from flask import Flask, flash, g, redirect, render_template, request, session
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config
from db import get_db, init_db


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
        if not rows:
            try:
                from services.supabase_service import supabase_get_activities
                sb_rows = supabase_get_activities(session["user_id"], limit=6)
                if sb_rows:
                    rows = sb_rows
            except Exception:
                pass
        return render_template("dashboard.html", activities=rows)

    from routes.auth import auth_bp
    from routes.resume import resume_bp
    from routes.interview import interview_bp
    from routes.career import career_bp
    from routes.jobs import jobs_bp
    from routes.builder import builder_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(career_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(builder_bp)
    return app


# Top-level Flask app instance required by Vercel and WSGI runtimes
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
