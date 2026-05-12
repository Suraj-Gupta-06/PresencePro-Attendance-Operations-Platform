"""Students API routes."""
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services import student_service
from src.utils.helpers import success_response, error_response, paginate_query
from src.utils.decorators import teacher_or_admin, admin_required
from src.utils.validators import validate_email, validate_student_id, allowed_file
from src.models.class_model import Class

students_bp = Blueprint("students", __name__)


@students_bp.post("/")
@jwt_required()
@teacher_or_admin
def create_student():
    form = request.form
    files = request.files.getlist("images")

    required = ["student_id", "name", "email"]
    missing = [f for f in required if not form.get(f)]
    if missing:
        return error_response(f"Missing required fields: {', '.join(missing)}")
    if not validate_email(form.get("email", "")):
        return error_response("Invalid email format.")
    if not validate_student_id(form.get("student_id", "")):
        return error_response("Student ID must be 3-20 alphanumeric characters.")
    if not files:
        return error_response("At least 1 face image is required.")

    valid_images = [f.read() for f in files if f and allowed_file(f.filename)]
    if not valid_images:
        return error_response("No valid image files (JPEG/PNG) found.")

    data = {
        "student_id": form.get("student_id").strip().upper(),
        "name": form.get("name").strip(),
        "email": form.get("email").strip().lower(),
        "phone": form.get("phone", "").strip() or None,
        "department": form.get("department", "").strip() or None,
        "class_id": int(form.get("class_id")) if form.get("class_id") else None,
        "roll_no": form.get("roll_no", "").strip() or None,
        "dob": form.get("dob", "").strip() or None,
        "gender": form.get("gender", "").strip() or None,
    }

    student, err = student_service.create_student(data, valid_images)
    if err:
        status = 409 if "already" in err else 400
        return error_response(err, status)

    return success_response({
        "id": student.id,
        "student_id": student.student_id,
        "name": student.name,
        "profile_image": student.profile_image,
        "embeddings_generated": student.embeddings.count(),
    }, "Student registered successfully.", 201)


@students_bp.get("/")
@jwt_required()
def list_students():
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 50)), 100)
    is_active_param = request.args.get("is_active")
    is_active = None
    if is_active_param is not None:
        is_active = is_active_param.lower() == "true"

    query = student_service.get_students(
        page=page, per_page=per_page,
        department=request.args.get("department"),
        class_id=request.args.get("class_id"),
        search=request.args.get("search"),
        is_active=is_active,
    )
    result = paginate_query(query, page, per_page, schema_fn=lambda s: s.to_dict(include_stats=True))
    return success_response(result)


@students_bp.get("/<int:student_db_id>")
@jwt_required()
def get_student(student_db_id):
    student = student_service.get_student(student_db_id)
    if not student:
        return error_response("Student not found.", 404)
    from src.services.attendance_service import get_student_attendance_stats
    stats = get_student_attendance_stats(student_db_id)
    data = student.to_dict()
    data["attendance_stats"] = stats
    data["face_images"] = [fi.image_path for fi in student.face_images]
    data["class"] = student.class_.to_dict() if student.class_ else None
    return success_response(data)


@students_bp.put("/<int:student_db_id>")
@jwt_required()
@teacher_or_admin
def update_student(student_db_id):
    data = request.get_json(silent=True) or {}
    student, err = student_service.update_student(student_db_id, data)
    if err:
        return error_response(err, 404)
    return success_response(student.to_dict(), "Student updated.")


@students_bp.delete("/<int:student_db_id>")
@jwt_required()
@admin_required
def delete_student(student_db_id):
    ok, err = student_service.delete_student(student_db_id)
    if not ok:
        return error_response(err, 404)
    return success_response(message="Student deactivated.")


@students_bp.post("/<int:student_db_id>/add-images")
@jwt_required()
@teacher_or_admin
def add_images(student_db_id):
    files = request.files.getlist("images")
    valid_images = [f.read() for f in files if f and allowed_file(f.filename)]
    if not valid_images:
        return error_response("No valid images provided.")
    added, err = student_service.add_images_to_student(student_db_id, valid_images)
    if err:
        return error_response(err, 404)
    return success_response({"images_added": added}, f"{added} images added.")


@students_bp.get("/classes")
@jwt_required()
def get_classes():
    classes = Class.query.order_by(Class.name).all()
    return success_response([c.to_dict() for c in classes])
