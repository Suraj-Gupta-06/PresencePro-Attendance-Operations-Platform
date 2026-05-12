"""Input validators."""
import re
from datetime import datetime


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple:
    """Returns (valid: bool, reason: str)."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, "OK"


def validate_student_id(sid: str) -> bool:
    """Alphanumeric, 3-20 chars."""
    return bool(re.match(r"^[A-Za-z0-9]{3,20}$", sid))


def validate_phone(phone: str) -> bool:
    return bool(re.match(r"^\+?[\d\s\-]{7,15}$", phone))


def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def allowed_file(filename: str, allowed: set = None) -> bool:
    if allowed is None:
        allowed = {"jpg", "jpeg", "png", "webp"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed
