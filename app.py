import os
import secrets
from functools import wraps

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from vpn_service import VPNService


def create_app(vpn_service: VPNService = None) -> Flask:
    app = Flask(__name__)
    secret_key = os.environ.get("FLASK_SECRET_KEY")
    if not secret_key:
        app.logger.warning(
            "FLASK_SECRET_KEY is not set; using an ephemeral key for this process."
        )
        secret_key = secrets.token_hex(32)
    app.config["SECRET_KEY"] = secret_key
    app.config["VPN_WEB_TOKEN"] = os.environ.get("VPN_WEB_TOKEN")
    app.config["VPN_SERVICE"] = vpn_service or VPNService(
        allowed_config_dir=os.environ.get("VPN_CONFIG_DIR"),
        log_path=os.environ.get("VPN_LOG_PATH"),
    )

    def token_authorized() -> bool:
        expected = app.config["VPN_WEB_TOKEN"]
        if not expected:
            return True
        provided = request.form.get("access_token")
        if provided is None:
            provided = request.headers.get("X-VPN-TOKEN")
        if provided is None:
            return False
        return secrets.compare_digest(provided, expected)

    def require_token(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not token_authorized():
                return "Unauthorized", 403
            return view(*args, **kwargs)

        return wrapped

    @app.get("/")
    def index():
        status = app.config["VPN_SERVICE"].status()
        return render_template(
            "index.html",
            status=status,
            auth_required=bool(app.config["VPN_WEB_TOKEN"]),
        )

    @app.post("/connect")
    @require_token
    def connect():
        service = app.config["VPN_SERVICE"]
        success, message = service.connect(
            config_path=request.form.get("config_path", "").strip(),
        )
        flash(message, "success" if success else "error")
        return redirect(url_for("index"))

    @app.post("/disconnect")
    @require_token
    def disconnect():
        service = app.config["VPN_SERVICE"]
        success, message = service.disconnect()
        flash(message, "success" if success else "error")
        return redirect(url_for("index"))

    @app.get("/api/status")
    @require_token
    def api_status():
        return jsonify(app.config["VPN_SERVICE"].status())

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )
