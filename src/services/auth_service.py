"""Auth service — login, register, token management."""
from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from app import db, bcrypt
from src.models.user import User
from src.models.audit_log import AuditLog
from src.utils.helpers import get_client_ip


def register_user(username: str, email: str, password: str, role: str = "student"):
    if User.query.filter_by(email=email).first():
        return None, "Email already registered."
    if User.query.filter_by(username=username).first():
        return None, "Username already taken."
    if role not in User.VALID_ROLES:
        return None, f"Invalid role. Must be one of: {', '.join(User.VALID_ROLES)}"

    hashed = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, email=email, password_hash=hashed, role=role)
    db.session.add(user)
    db.session.commit()
    return user, None


def login_user(email: str, password: str):
    user = User.query.filter_by(email=email).first()

    if not user:
        return None, None, "Invalid credentials."

    # Check lockout
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds() // 60) + 1
        return None, None, f"Account locked. Try again in {remaining} minute(s)."

    if not user.is_active:
        return None, None, "Account is inactive."

    if not bcrypt.check_password_hash(user.password_hash, password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            user.failed_login_attempts = 0
        db.session.commit()
        return None, None, "Invalid credentials."

    # Successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    log = AuditLog(user_id=user.id, action="LOGIN",
                   entity_type="user", entity_id=user.id,
                   ip_address=get_client_ip())
    db.session.add(log)
    db.session.commit()

    return user, {"access_token": access_token, "refresh_token": refresh_token}, None


def get_user_by_id(user_id: int):
    return User.query.get(user_id)
