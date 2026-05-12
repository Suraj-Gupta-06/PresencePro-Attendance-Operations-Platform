"""Attendance service — marking, cooldown, history."""
from datetime import timedelta
from app import db
from src.models.attendance import Attendance
from src.models.student import Student
from src.utils.helpers import get_local_now, get_local_date, current_session


def check_cooldown(student_db_id: int, cooldown_minutes: int = 120) -> bool:
    """Return True if student is within cooldown period (attendance already marked)."""
    cutoff = get_local_now() - timedelta(minutes=cooldown_minutes)
    recent = Attendance.query.filter(
        Attendance.student_id == student_db_id,
        Attendance.timestamp >= cutoff
    ).first()
    return recent is not None


def mark_attendance(student_db_id: int, confidence: float = None,
                    session: str = None, location: str = None,
                    image_path: str = None, method: str = "Auto",
                    status: str = "Present", marked_by: int = None,
                    notes: str = None, cooldown_minutes: int = 120) -> tuple:
    """
    Mark attendance for a student.
    Returns (attendance_record, error_message).
    """
    student = Student.query.get(student_db_id)
    if not student:
        return None, "Student not found."
    if not student.is_active:
        return None, "Student account is inactive."

    # Cooldown check (skip for manual entries with override)
    if method == "Auto" and check_cooldown(student_db_id, cooldown_minutes):
        return None, "DUPLICATE"  # Caller handles this gracefully

    if session is None:
        session = current_session()

    today = get_local_date()
    record = Attendance(
        student_id=student_db_id,
        date=today,
        timestamp=get_local_now(),
        session=session,
        confidence=confidence,
        location=location,
        image_path=image_path,
        method=method,
        status=status,
        marked_by=marked_by,
        notes=notes,
    )
    db.session.add(record)
    db.session.commit()
    return record, None


def get_attendance(start_date=None, end_date=None, student_id=None,
                   session=None, status=None, page=1, per_page=50):
    query = Attendance.query
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    if student_id:
        query = query.filter_by(student_id=student_id)
    if session:
        query = query.filter_by(session=session)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Attendance.timestamp.desc())


def get_today_summary():
    today = get_local_date()
    total = Student.query.filter_by(is_active=True).count()
    present_ids = (
        db.session.query(Attendance.student_id)
        .filter(Attendance.date == today, Attendance.status == "Present")
        .distinct()
        .all()
    )
    present = len(present_ids)
    return {
        "date": today.isoformat(),
        "total_students": total,
        "present": present,
        "absent": total - present,
        "percentage": round(present / total * 100, 2) if total else 0,
    }


def get_student_attendance_stats(student_db_id: int,
                                  start_date=None, end_date=None) -> dict:
    query = Attendance.query.filter_by(student_id=student_db_id, status="Present")
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)

    records = query.all()
    present_days = len(set(r.date for r in records))

    # Total unique attendance days across all students
    total_query = db.session.query(Attendance.date).filter(
        Attendance.status == "Present"
    ).distinct()
    if start_date:
        total_query = total_query.filter(Attendance.date >= start_date)
    if end_date:
        total_query = total_query.filter(Attendance.date <= end_date)
    total_days = total_query.count()

    pct = round(present_days / total_days * 100, 2) if total_days else 0
    return {
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": total_days - present_days,
        "percentage": pct,
    }
