"""Database initialisation script.

Run once: python init_db.py

Creates all tables and inserts:
    - Admin user (prompted or env)
    - Default classes
    - Default system config values
"""
import os
import sys
from getpass import getpass

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db, bcrypt
from src.models import User, Class, SystemConfig

def _get_admin_credentials():
    email = os.getenv("ADMIN_EMAIL") or input("Admin email: ").strip()
    if not email:
        raise ValueError("Admin email is required.")
    password = os.getenv("ADMIN_PASSWORD") or getpass("Admin password: ").strip()
    if not password:
        raise ValueError("Admin password is required.")
    confirm = os.getenv("ADMIN_PASSWORD") or getpass("Confirm password: ").strip()
    if password != confirm:
        raise ValueError("Passwords do not match.")
    return email, password


def init_database():
    # Ensure directories exist BEFORE creating the app context
    import os as _os
    _base = _os.path.abspath(_os.path.dirname(__file__))
    for _d in ["data/database", "data/faces", "data/attendance_captures", "logs"]:
        _os.makedirs(_os.path.join(_base, _d), exist_ok=True)

    app = create_app("development")
    with app.app_context():
        print("Creating all tables …")
        db.create_all()

        # ── Admin user ──────────────────────────────────────────────
        try:
            admin_email, admin_password = _get_admin_credentials()
        except ValueError as exc:
            print(f"  [ERROR] {exc}")
            print("  [ABORT] Admin user was not created.")
            return

        if not User.query.filter_by(email=admin_email).first():
            admin = User(
                username="admin",
                email=admin_email,
                password_hash=bcrypt.generate_password_hash(admin_password).decode("utf-8"),
                role="admin",
                is_active=True,
            )
            db.session.add(admin)
            print("  [OK] Admin user created.")
        else:
            print("  [--] Admin user already exists, skipping.")

        # ── Default classes ─────────────────────────────────────────
        default_classes = [
            {"name": "Computer Science A", "department": "Computer Science", "semester": "Fall 2026", "year": 2026},
            {"name": "Electronics B", "department": "Electronics", "semester": "Fall 2026", "year": 2026},
            {"name": "Mechanical C", "department": "Mechanical", "semester": "Fall 2026", "year": 2026},
        ]
        for cls_data in default_classes:
            if not Class.query.filter_by(name=cls_data["name"]).first():
                cls = Class(**cls_data)
                db.session.add(cls)
        print("  [OK] Default classes created.")

        # ── System config defaults ───────────────────────────────────
        configs = [
            ("recognition_threshold", "0.5", "float", "Face recognition similarity threshold (lower = stricter)"),
            ("cooldown_period", "120", "int", "Attendance cooldown in minutes"),
            ("camera_resolution", "1280x720", "string", "Default camera resolution"),
            ("detection_model", "hog", "string", "Face detection model: hog or cnn"),
            ("frame_skip", "2", "int", "Process every Nth frame"),
            ("grace_period", "10", "int", "Late arrival grace period in minutes"),
            ("min_face_images", "5", "int", "Minimum face images required for registration"),
            ("session_morning_start", "08:00", "string", "Morning session start time"),
            ("session_afternoon_start", "12:00", "string", "Afternoon session start time"),
            ("session_evening_start", "16:00", "string", "Evening session start time"),
        ]
        for key, value, dtype, desc in configs:
            if not SystemConfig.query.filter_by(key=key).first():
                SystemConfig.set(key, value, dtype, desc)
        print("  [OK] Default system configuration set.")

        db.session.commit()
        print("\n[SUCCESS] Database initialised successfully!")
        print("\nAdmin account initialised.")


if __name__ == "__main__":
    init_database()
