"""Analytics API routes."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from datetime import datetime
from src.services import analytics_service
from src.utils.helpers import success_response, error_response

analytics_bp = Blueprint("analytics", __name__)


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


@analytics_bp.get("/overview")
@jwt_required()
def overview():
    start = _parse_date(request.args.get("start_date"))
    end = _parse_date(request.args.get("end_date"))
    data = analytics_service.get_overview(start, end)
    return success_response(data)


@analytics_bp.get("/student/<int:student_db_id>")
@jwt_required()
def student_analytics(student_db_id):
    data = analytics_service.get_student_analytics(student_db_id)
    if not data:
        return error_response("Student not found.", 404)
    return success_response(data)


@analytics_bp.get("/absentees")
@jwt_required()
def top_absentees():
    limit = int(request.args.get("limit", 10))
    data = analytics_service.get_top_absentees(limit)
    return success_response(data)
