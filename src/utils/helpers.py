"""General helper utilities."""
import os
import uuid
import base64
from datetime import datetime, date
try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - fallback for older runtimes
    ZoneInfo = None
import cv2
import numpy as np
from flask import request, jsonify


def success_response(data=None, message="Success", status_code=200):
    resp = {"success": True, "message": message}
    if data is not None:
        resp["data"] = data
    return jsonify(resp), status_code


def error_response(message="An error occurred", status_code=400, error=None):
    resp = {"success": False, "message": message}
    if error:
        resp["error"] = str(error)
    return jsonify(resp), status_code


def paginate_query(query, page: int, per_page: int, schema_fn=None):
    """Return paginated results dict from a SQLAlchemy query."""
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    items = [schema_fn(i) if schema_fn else i for i in paginated.items]
    return {
        "items": items,
        "pagination": {
            "page": paginated.page,
            "per_page": paginated.per_page,
            "total": paginated.total,
            "pages": paginated.pages,
            "has_next": paginated.has_next,
            "has_prev": paginated.has_prev,
        },
    }


def save_image(image_data: bytes, folder: str, filename: str = None) -> str:
    """Save raw image bytes to folder; returns relative path."""
    os.makedirs(folder, exist_ok=True)
    if filename is None:
        filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f:
        f.write(image_data)
    return filepath


def save_cv2_image(img: np.ndarray, folder: str, filename: str = None) -> str:
    """Save OpenCV BGR image to folder; returns full path."""
    os.makedirs(folder, exist_ok=True)
    if filename is None:
        filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(folder, filename)
    cv2.imwrite(filepath, img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return filepath


def decode_base64_image(b64_string: str) -> np.ndarray:
    """Decode base64-encoded image (from webcam capture) to BGR numpy array."""
    # Remove data URI prefix if present
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]
    img_bytes = base64.b64decode(b64_string)
    nparr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


def get_client_ip() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def current_session() -> str:
    """Determine Morning / Afternoon / Evening from current time."""
    hour = get_local_now().hour
    if hour < 12:
        return "Morning"
    elif hour < 17:
        return "Afternoon"
    return "Evening"


def _get_timezone():
    tz_name = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
    if ZoneInfo:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            return None
    return None


def get_local_now() -> datetime:
    tz = _get_timezone()
    return datetime.now(tz) if tz else datetime.now()


def get_local_date() -> date:
    return get_local_now().date()
