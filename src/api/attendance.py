"""Attendance API routes."""
from datetime import date, datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services import attendance_service
from src.utils.helpers import success_response, error_response, paginate_query
from src.utils.decorators import teacher_or_admin, admin_required
from src.models.system_config import SystemConfig

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.post("/mark")
@jwt_required()
def mark_attendance():
    data = request.get_json(silent=True) or {}
    student_db_id = data.get("student_id")
    if not student_db_id:
        return error_response("student_id is required.")

    cooldown = SystemConfig.get("cooldown_period", 120)
    record, err = attendance_service.mark_attendance(
        student_db_id=int(student_db_id),
        confidence=data.get("confidence"),
        session=data.get("session"),
        location=data.get("location"),
        image_path=data.get("image_path"),
        method="Auto",
        cooldown_minutes=int(cooldown),
    )
    if err == "DUPLICATE":
        return error_response("Attendance already marked within cooldown period.", 409)
    if err:
        return error_response(err)
    return success_response(record.to_dict(), "Attendance marked.", 201)


@attendance_bp.post("/manual")
@jwt_required()
@teacher_or_admin
def manual_attendance():
    data = request.get_json(silent=True) or {}
    user_id = get_jwt_identity()
    student_db_id = data.get("student_id")
    if not student_db_id:
        return error_response("student_id is required.")

    record, err = attendance_service.mark_attendance(
        student_db_id=int(student_db_id),
        session=data.get("session", "Morning"),
        method="Manual",
        status=data.get("status", "Present"),
        marked_by=user_id,
        notes=data.get("notes"),
        cooldown_minutes=0,
    )
    if err:
        return error_response(err)
    return success_response(record.to_dict(), "Manual attendance marked.", 201)


@attendance_bp.get("/")
@jwt_required()
def get_attendance():
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 50)), 100)

    start_date = None
    end_date = None
    try:
        if request.args.get("start_date"):
            start_date = datetime.strptime(request.args.get("start_date"), "%Y-%m-%d").date()
        if request.args.get("end_date"):
            end_date = datetime.strptime(request.args.get("end_date"), "%Y-%m-%d").date()
    except ValueError:
        return error_response("Invalid date format. Use YYYY-MM-DD.")

    student_id = request.args.get("student_id")
    query = attendance_service.get_attendance(
        start_date=start_date,
        end_date=end_date,
        student_id=int(student_id) if student_id else None,
        session=request.args.get("session"),
        status=request.args.get("status"),
    )
    result = paginate_query(query, page, per_page, schema_fn=lambda a: a.to_dict())
    return success_response(result)


@attendance_bp.get("/today")
@jwt_required()
def today_summary():
    from src.models.attendance import Attendance as AttModel
    from datetime import date as dt
    summary = attendance_service.get_today_summary()
    records = AttModel.query.filter_by(date=dt.today()).order_by(AttModel.timestamp.desc()).limit(20).all()
    summary["recent"] = [r.to_dict() for r in records]
    return success_response(summary)


@attendance_bp.get("/student/<int:student_db_id>")
@jwt_required()
def student_attendance(student_db_id):
    from src.models.attendance import Attendance as AttModel
    stats = attendance_service.get_student_attendance_stats(student_db_id)
    records = AttModel.query.filter_by(student_id=student_db_id).order_by(AttModel.date.desc()).limit(60).all()
    return success_response({
        "summary": stats,
        "records": [r.to_dict() for r in records],
    })


@attendance_bp.delete("/<int:att_id>")
@jwt_required()
@admin_required
def delete_attendance(att_id):
    from src.models.attendance import Attendance as AttModel
    from app import db
    record = AttModel.query.get(att_id)
    if not record:
        return error_response("Record not found.", 404)
    db.session.delete(record)
    db.session.commit()
    return success_response(message="Attendance record deleted.")
