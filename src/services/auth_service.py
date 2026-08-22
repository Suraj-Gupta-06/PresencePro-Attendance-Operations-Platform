"""Auth service — login, register, token management."""
from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from app import db, bcrypt
from src.models.user import User
from src.models.audit_log import AuditLog
from src.utils.helpers import get_client_ip
from src.utils.validators import validate_password


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


def update_admin_credentials(
    user_id: int,
    username: str = None,
    current_password: str = None,
    new_password: str = None,
):
    user = User.query.get(user_id)
    if not user:
        return None, 404, "User not found."

    username = (username or "").strip()
    current_password = current_password or ""
    new_password = new_password or ""

    if not username and not new_password:
        return None, 400, "Provide at least a new username or new password."

    if username:
        if len(username) < 3 or len(username) > 50:
            return None, 400, "Username must be between 3 and 50 characters."
        existing = User.query.filter(User.username == username, User.id != user.id).first()
        if existing:
            return None, 409, "Username already taken."

    if new_password:
        if not current_password:
            return None, 400, "Current password is required to set a new password."
        if not bcrypt.check_password_hash(user.password_hash, current_password):
            return None, 401, "Current password is incorrect."
        valid_pw, reason = validate_password(new_password)
        if not valid_pw:
            return None, 400, reason
        user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")

    if username:
        user.username = username

    db.session.add(user)
    db.session.add(AuditLog(
        user_id=user.id,
        action="ADMIN_PROFILE_UPDATE",
        entity_type="user",
        entity_id=user.id,
        ip_address=get_client_ip(),
    ))
    db.session.commit()

    return user, 200, None
