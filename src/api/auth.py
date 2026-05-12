"""Auth API routes."""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, create_access_token, jwt_required
from src.services import auth_service
from src.utils.validators import validate_email, validate_password
from src.utils.helpers import success_response, error_response

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role", "student")

    if not all([username, email, password]):
        return error_response("username, email and password are required.")
    if not validate_email(email):
        return error_response("Invalid email format.")
    valid_pw, reason = validate_password(password)
    if not valid_pw:
        return error_response(reason)

    user, err = auth_service.register_user(username, email, password, role)
    if err:
        return error_response(err, 409)
    return success_response(user.to_dict(), "User registered successfully.", 201)


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return error_response("Email and password are required.")

    user, tokens, err = auth_service.login_user(email, password)
    if err:
        return error_response(err, 401)

    return success_response({
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": "Bearer",
        "user": user.to_dict(),
    }, "Login successful.")


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=str(user_id))
    return success_response({"access_token": access_token})


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = auth_service.get_user_by_id(user_id)
    if not user:
        return error_response("User not found.", 404)
    return success_response(user.to_dict())
