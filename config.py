import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ── Core ──────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    DEBUG = False
    TESTING = False

    # ── Database ───────────────────────────────────────────────────────
    _db_path = os.path.join(BASE_DIR, "data", "database", "attendance.db")
    os.makedirs(os.path.dirname(_db_path), exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + _db_path.replace("\\", "/"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # ── JWT ────────────────────────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 604800))
    )

    # ── File Storage ───────────────────────────────────────────────────
    FACES_FOLDER = os.path.join(BASE_DIR, os.getenv("FACES_FOLDER", "data/faces"))
    ATTENDANCE_CAPTURES_FOLDER = os.path.join(
        BASE_DIR, os.getenv("ATTENDANCE_CAPTURES_FOLDER", "data/attendance_captures")
    )
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_SIZE", 5 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    # ── ML / Recognition ───────────────────────────────────────────────
    RECOGNITION_THRESHOLD = float(os.getenv("RECOGNITION_THRESHOLD", 0.5))
    COOLDOWN_PERIOD = int(os.getenv("COOLDOWN_PERIOD", 120))  # minutes
    FRAME_SKIP = int(os.getenv("FRAME_SKIP", 2))
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))

    # ── CORS ───────────────────────────────────────────────────────────
    CORS_ORIGINS = ["http://localhost:5000", "http://127.0.0.1:5000"]

    # ── Timezone ──────────────────────────────────────────────────────
    TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Kolkata")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
