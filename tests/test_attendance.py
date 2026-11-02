"""Unit tests for attendance operations and cooldown rules."""
import json
from src.models import Student


def test_get_today_attendance(client, admin_headers):
    """Test fetching today's attendance summary."""
    resp = client.get("/api/v1/attendance/today", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "present" in data["data"]


def test_manual_attendance_mark_and_cooldown(app, client, admin_headers):
    """Test manual attendance submission and duplicate check."""
    with app.app_context():
        student = Student.query.filter_by(student_id="CS2026001").first()
        student_db_id = student.id

    # 1. Mark attendance first time
    resp = client.post("/api/v1/attendance/manual", headers=admin_headers, json={
        "student_id": student_db_id,
        "session": "Morning",
        "status": "Present",
        "notes": "Test manual mark",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True

    # 2. Mark attendance second time without override - should report duplicate/cooldown
    resp2 = client.post("/api/v1/attendance/manual", headers=admin_headers, json={
        "student_id": student_db_id,
        "session": "Morning",
        "status": "Present",
        "override": False,
    })
    data2 = resp2.get_json()
    # Cooldown blocks or returns error response
    assert data2["success"] is False or resp2.status_code in [400, 409]
