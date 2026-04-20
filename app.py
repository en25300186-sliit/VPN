import os

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from vpn_service import VPNService


def create_app(vpn_service: VPNService = None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "change-me")
    app.config["VPN_SERVICE"] = vpn_service or VPNService()

    @app.get("/")
    def index():
        status = app.config["VPN_SERVICE"].status()
        return render_template("index.html", status=status)

    @app.post("/connect")
    def connect():
        service = app.config["VPN_SERVICE"]
        success, message = service.connect(
            config_path=request.form.get("config_path", "").strip(),
            username=request.form.get("username", "").strip() or None,
            password=request.form.get("password", "").strip() or None,
        )
        flash(message, "success" if success else "error")
        return redirect(url_for("index"))

    @app.post("/disconnect")
    def disconnect():
        service = app.config["VPN_SERVICE"]
        success, message = service.disconnect()
        flash(message, "success" if success else "error")
        return redirect(url_for("index"))

    @app.get("/api/status")
    def api_status():
        return jsonify(app.config["VPN_SERVICE"].status())

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
    )
