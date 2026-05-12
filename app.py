"""
Main Flask application factory.
"""
import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt

from config import config

# ── Extension instances (bound to app in create_app) ─────────────────────────
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
bcrypt = Bcrypt()


def create_app(config_name: str = None) -> Flask:
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
        if config_name not in config:
            config_name = "development"

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # ── Ensure data dirs exist ────────────────────────────────────────
    os.makedirs(app.config["FACES_FOLDER"], exist_ok=True)
    os.makedirs(app.config["ATTENDANCE_CAPTURES_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "data", "database"), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)

    # ── Init extensions ───────────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # ── Register API blueprints ───────────────────────────────────────
    from src.api.auth import auth_bp
    from src.api.students import students_bp
    from src.api.attendance import attendance_bp
    from src.api.recognition import recognition_bp
    from src.api.analytics import analytics_bp
    from src.api.config_api import config_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(students_bp, url_prefix="/api/v1/students")
    app.register_blueprint(attendance_bp, url_prefix="/api/v1/attendance")
    app.register_blueprint(recognition_bp, url_prefix="/api/v1/recognize")
    app.register_blueprint(analytics_bp, url_prefix="/api/v1/analytics")
    app.register_blueprint(config_bp, url_prefix="/api/v1/config")

    # ── Register page blueprints ──────────────────────────────────────
    from src.views import views_bp
    app.register_blueprint(views_bp)

    # ── Root redirect ─────────────────────────────────────────────────
    @app.route("/")
    def root():
        return redirect(url_for("views.dashboard"))

    return app
