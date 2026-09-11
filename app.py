from flask import Flask, flash, g, redirect, render_template, request, session
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config
from db import get_db, init_db


import gzip

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000
    Config.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    Config.DATABASE.parent.mkdir(parents=True, exist_ok=True)
    init_db()

    @app.after_request
    def apply_performance_headers(response):
        # 1. Aggressive immutable caching for static assets
        if request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif response.status_code == 200 and request.method == "GET" and not request.path.startswith("/auth/"):
            response.headers["Cache-Control"] = "public, max-age=0, must-revalidate"

        # 2. Dynamic Gzip compression for textual responses over 400 bytes
        accept_encoding = request.headers.get("Accept-Encoding", "")
        if (
            "gzip" in accept_encoding.lower()
            and response.status_code == 200
            and not response.direct_passthrough
            and response.content_type
            and any(t in response.content_type for t in ("text/html", "text/css", "application/javascript", "application/json", "image/svg+xml"))
        ):
            data = response.get_data()
            if len(data) > 400:
                compressed = gzip.compress(data, compresslevel=6)
                if len(compressed) < len(data):
                    response.set_data(compressed)
                    response.headers["Content-Encoding"] = "gzip"
                    response.headers["Content-Length"] = len(compressed)
                    response.headers["Vary"] = "Accept-Encoding"

        return response

    @app.get("/sw.js")
    def service_worker():
        response = app.send_static_file("sw.js")
        response.headers["Content-Type"] = "application/javascript; charset=utf-8"
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"
        return response

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
    from routes.jobs import jobs_bp
    from routes.builder import builder_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(builder_bp)
    return app


# Top-level Flask app instance required by Vercel and WSGI runtimes
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
