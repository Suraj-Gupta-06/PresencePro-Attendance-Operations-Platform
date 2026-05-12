"""Analytics service — charts, summaries, trends."""
from datetime import timedelta
from sqlalchemy import func
from app import db
from src.models.attendance import Attendance
from src.models.student import Student
from src.utils.helpers import get_local_date


def get_overview(start_date=None, end_date=None) -> dict:
    if not start_date:
        start_date = get_local_date() - timedelta(days=30)
    if not end_date:
        end_date = get_local_date()

    total_students = Student.query.filter_by(is_active=True).count()

    # Daily attendance percentages
    daily_rows = (
        db.session.query(
            Attendance.date,
            func.count(func.distinct(Attendance.student_id)).label("present"),
        )
        .filter(
            Attendance.date.between(start_date, end_date),
            Attendance.status == "Present",
        )
        .group_by(Attendance.date)
        .order_by(Attendance.date)
        .all()
    )

    attendance_by_day = []
    for row in daily_rows:
        pct = round(row.present / total_students * 100, 1) if total_students else 0
        attendance_by_day.append({
            "date": row.date.isoformat(),
            "present": row.present,
            "percentage": pct,
        })

    # Department breakdown
    dept_rows = (
        db.session.query(
            Student.department,
            func.count(func.distinct(Attendance.student_id)).label("present_students"),
            func.count(func.distinct(Student.id)).label("total_students"),
        )
        .join(Attendance, Attendance.student_id == Student.id, isouter=True)
        .filter(
            db.or_(Attendance.date == None,
                   Attendance.date.between(start_date, end_date))
        )
        .group_by(Student.department)
        .all()
    )
    department_stats = [
        {
            "department": row.department or "Unknown",
            "present_students": row.present_students or 0,
            "total_students": row.total_students or 0,
            "percentage": round((row.present_students or 0) / row.total_students * 100, 1)
            if row.total_students else 0,
        }
        for row in dept_rows
    ]

    avg_pct = (
        round(sum(d["percentage"] for d in attendance_by_day) / len(attendance_by_day), 1)
        if attendance_by_day else 0
    )

    return {
        "total_students": total_students,
        "avg_attendance_percentage": avg_pct,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "attendance_by_day": attendance_by_day,
        "department_stats": department_stats,
    }


def get_student_analytics(student_db_id: int) -> dict:
    student = Student.query.get(student_db_id)
    if not student:
        return {}

    thirty_days_ago = get_local_date() - timedelta(days=30)

    records = (
        Attendance.query
        .filter_by(student_id=student_db_id, status="Present")
        .filter(Attendance.date >= thirty_days_ago)
        .order_by(Attendance.date)
        .all()
    )

    # Weekly breakdown
    weeks = {}
    for r in records:
        week_start = r.date - timedelta(days=r.date.weekday())
        key = week_start.isoformat()
        weeks.setdefault(key, 0)
        weeks[key] += 1

    trend = [{"week": k, "days_present": v} for k, v in sorted(weeks.items())]

    # Session breakdown
    session_counts = {"Morning": 0, "Afternoon": 0, "Evening": 0}
    for r in records:
        if r.session in session_counts:
            session_counts[r.session] += 1

    total_days = db.session.query(func.count(func.distinct(Attendance.date))).scalar() or 0
    present_days = len(set(r.date for r in Attendance.query.filter_by(
        student_id=student_db_id, status="Present").all()))
    pct = round(present_days / total_days * 100, 1) if total_days else 0

    return {
        "student": student.to_dict(),
        "attendance_percentage": pct,
        "total_days": total_days,
        "present_days": present_days,
        "trend": trend,
        "session_breakdown": session_counts,
    }


def get_top_absentees(limit=10) -> list:
    total_days = db.session.query(func.count(func.distinct(Attendance.date))).scalar() or 1
    students = Student.query.filter_by(is_active=True).all()
    results = []
    for s in students:
        present = s.attendance_records.filter_by(status="Present").count()
        pct = round(present / total_days * 100, 1)
        results.append({"student": s.to_dict(), "present_days": present, "percentage": pct})
    results.sort(key=lambda x: x["percentage"])
    return results[:limit]
