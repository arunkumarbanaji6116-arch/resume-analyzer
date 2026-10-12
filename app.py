import gzip
import logging
from flask import Flask, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config
from db import get_db, init_db
from services.limiter import limiter
from services.security import login_required

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000

    # 1. Initialize CORS with strict origin validation
    CORS(
        app,
        origins=Config.ALLOWED_ORIGINS,
        supports_credentials=True,
        resources={r"/*": {"origins": Config.ALLOWED_ORIGINS}}
    )

    # 2. Initialize Rate Limiter
    limiter.init_app(app)

    # 3. Ensure required directories exist and initialize database schema
    Config.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    Config.DATABASE.parent.mkdir(parents=True, exist_ok=True)
    init_db()

    @app.after_request
    def apply_security_and_performance_headers(response):
        # --- DEFENSIVE SECURITY HEADERS (OWASP ASVS Standard) ---
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(self), payment=()"

        # Content Security Policy (prevents cross-site script exfiltration & clickjacking)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://pagead2.googlesyndication.com https://*.googlesyndication.com https://*.google.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' https://api.github.com https://api.elevenlabs.io https://*.supabase.co https://pagead2.googlesyndication.com https://*.google.com; "
            "frame-src 'self' https://googleads.g.doubleclick.net https://*.googlesyndication.com https://*.google.com; "
            "media-src 'self' blob: data: https://api.elevenlabs.io; "
            "frame-ancestors 'self';"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        # Enforce HSTS for production domains
        if not (app.debug or Config.FLASK_DEBUG):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # --- PERFORMANCE & CACHING HEADERS ---
        if request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif response.status_code == 200 and request.method == "GET" and not request.path.startswith("/auth/"):
            response.headers["Cache-Control"] = "public, max-age=0, must-revalidate"

        # Dynamic Gzip compression for textual responses over 400 bytes
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

    @app.errorhandler(429)
    def handle_ratelimit_exceeded(_error):
        """Custom rate limit handler with JSON and HTML fallback."""
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({
                "success": False,
                "error": "Too Many Requests",
                "message": "Rate limit reached. Please wait a moment before sending another request."
            }), 429
        flash("Rate limit reached. Please wait a moment before submitting again.", "error")
        return redirect(request.referrer or url_for("landing")), 429

    @app.errorhandler(403)
    def handle_forbidden(_error):
        """Custom 403 Forbidden handler with JSON and HTML fallback."""
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({
                "success": False,
                "error": "Forbidden",
                "message": "Access denied. Administrator privileges required."
            }), 403
        flash("Access denied: Administrator privileges required.", "error")
        return render_template("landing.html"), 403

    @app.get("/sw.js")
    def service_worker():
        response = app.send_static_file("sw.js")
        response.headers["Content-Type"] = "application/javascript; charset=utf-8"
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"
        return response

    @app.get("/ads.txt")
    def ads_txt():
        response = app.send_static_file("ads.txt")
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    @app.teardown_appcontext
    def close_db(_error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_upload(_error):
        flash("Uploaded files must be 8 MB or smaller.", "error")
        return redirect(request.url)

    @app.context_processor
    def inject_user():
        from services.security import is_admin_user
        return {
            "current_user": session.get("user"),
            "is_admin": is_admin_user(),
        }

    @app.get("/")
    def landing():
        return render_template("landing.html")

    @app.get("/dashboard")
    @login_required
    def dashboard():
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
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(builder_bp)
    app.register_blueprint(admin_bp)

    return app


# Top-level Flask app instance required by Vercel and WSGI runtimes
app = create_app()

if __name__ == "__main__":
    # Debug mode is explicitly bound to Config.FLASK_DEBUG (defaulting to False)
    app.run(debug=Config.FLASK_DEBUG)
