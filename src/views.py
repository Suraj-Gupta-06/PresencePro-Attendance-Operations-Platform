"""Views blueprint — serves HTML pages."""
from flask import Blueprint, render_template, redirect, url_for, send_from_directory
import os

views_bp = Blueprint("views", __name__)


@views_bp.get("/login")
def login():
    return render_template("login.html")


@views_bp.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@views_bp.get("/students")
def students():
    return render_template("students/list.html")


@views_bp.get("/students/register")
def register_student():
    return render_template("students/register.html")


@views_bp.get("/students/<int:student_id>")
def student_detail(student_id):
    return render_template("students/detail.html", student_id=student_id)


@views_bp.get("/attendance/mark")
def mark_attendance():
    return render_template("attendance/mark.html")


@views_bp.get("/attendance/history")
def attendance_history():
    return render_template("attendance/history.html")


@views_bp.get("/analytics")
def analytics():
    return render_template("analytics/reports.html")


@views_bp.get("/settings")
def settings():
    return render_template("settings.html")


# Serve uploaded face images
@views_bp.get("/data/faces/<path:filename>")
def serve_face_image(filename):
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "faces")
    return send_from_directory(base, filename)


@views_bp.get("/data/attendance_captures/<path:filename>")
def serve_capture(filename):
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "attendance_captures")
    return send_from_directory(base, filename)
