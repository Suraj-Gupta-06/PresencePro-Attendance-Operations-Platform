"""Utility decorators — JWT + role enforcement."""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from src.models.user import User


def jwt_required_custom(fn):
    """Require valid JWT; attach current user."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as e:
            return jsonify({"success": False, "error": "Authentication required", "message": str(e)}), 401
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    """Restrict endpoint to specified roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return jsonify({"success": False, "error": "Authentication required"}), 401

            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or user.role not in roles:
                return jsonify({
                    "success": False,
                    "error": f"Access denied. Required roles: {', '.join(roles)}"
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    return roles_required("admin")(fn)


def teacher_or_admin(fn):
    return roles_required("admin", "teacher")(fn)
