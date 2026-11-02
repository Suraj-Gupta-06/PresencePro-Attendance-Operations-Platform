"""Pytest configuration and fixtures for PresencePro test suite."""
import os
import sys
import pytest

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db, bcrypt
from src.models import User, Student, Class, SystemConfig
from flask_jwt_extended import create_access_token


@pytest.fixture
def app():
    """Create and configure a testing Flask app instance."""
    app = create_app("testing")

    with app.app_context():
        db.create_all()

        # Seed default test admin
        admin = User(
            username="admin",
            email="admin@test.com",
            password_hash=bcrypt.generate_password_hash("Admin@123").decode("utf-8"),
            role="admin",
            is_active=True,
        )
        db.session.add(admin)

        # Seed test class
        cls = Class(
            name="Computer Science A",
            department="Computer Science",
            semester="Fall 2026",
            year=2026,
        )
        db.session.add(cls)
        db.session.flush()

        # Seed test student
        student = Student(
            student_id="CS2026001",
            name="Alex Mercer",
            email="alex@test.com",
            department="Computer Science",
            class_id=cls.id,
            is_active=True,
        )
        db.session.add(student)

        # Default system configs
        SystemConfig.set("recognition_threshold", "0.5", "float")
        SystemConfig.set("cooldown_period", "120", "int")

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture
def admin_headers(app):
    """Generate JWT authorization headers for the test admin user."""
    with app.app_context():
        admin = User.query.filter_by(email="admin@test.com").first()
        token = create_access_token(
            identity=str(admin.id),
            additional_claims={"role": "admin", "email": admin.email}
        )
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
