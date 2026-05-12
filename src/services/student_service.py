"""Student service — CRUD, face image management."""
import os
import uuid
import cv2
import numpy as np
from flask import current_app
from app import db
from src.models.student import Student
from src.models.face_image import FaceImage
from src.models.embedding import FaceEmbedding
from src.ml.face_detection import detect_faces, crop_face
from src.ml.face_recognition_engine import generate_embedding_from_bgr
from src.ml.preprocessor import check_image_quality


def create_student(data: dict, image_files: list) -> tuple:
    """
    Register a new student with face images.
    Returns (student, error_message).
    """
    # Validate uniqueness
    if Student.query.filter_by(student_id=data["student_id"]).first():
        return None, "Student ID already exists."
    if Student.query.filter_by(email=data["email"]).first():
        return None, "Email already registered."

    student = Student(
        student_id=data["student_id"],
        name=data["name"],
        email=data["email"],
        phone=data.get("phone"),
        department=data.get("department"),
        class_id=data.get("class_id"),
        roll_no=data.get("roll_no"),
        gender=data.get("gender"),
    )
    if data.get("dob"):
        from datetime import datetime
        try:
            student.dob = datetime.strptime(data["dob"], "%Y-%m-%d").date()
        except ValueError:
            pass

    db.session.add(student)
    db.session.flush()  # Get student.id before commit

    faces_folder = os.path.join(current_app.config["FACES_FOLDER"], data["student_id"])
    os.makedirs(faces_folder, exist_ok=True)

    embeddings_added = 0
    profile_set = False

    for idx, img_bytes in enumerate(image_files):
        nparr = np.frombuffer(img_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is None:
            continue

        quality = check_image_quality(bgr)
        faces = detect_faces(bgr)
        if not faces:
            continue

        face = faces[0]
        face_crop = crop_face(bgr, face)
        if face_crop.size == 0:
            continue

        # Save image
        filename = f"img_{idx:03d}_{uuid.uuid4().hex[:6]}.jpg"
        img_path = os.path.join(faces_folder, filename)
        cv2.imwrite(img_path, face_crop, [cv2.IMWRITE_JPEG_QUALITY, 90])

        relative_path = f"data/faces/{data['student_id']}/{filename}"

        face_img = FaceImage(
            student_id=student.id,
            image_path=relative_path,
            angle="front",
            quality_score=quality.get("sharpness", 0.0),
        )
        db.session.add(face_img)

        if not profile_set:
            student.profile_image = relative_path
            profile_set = True

        # Generate embedding
        embedding = generate_embedding_from_bgr(face_crop)
        if embedding is not None:
            emb_record = FaceEmbedding(student_id=student.id)
            emb_record.embedding = embedding
            db.session.add(emb_record)
            embeddings_added += 1

    if embeddings_added == 0:
        db.session.rollback()
        return None, "No valid faces detected in uploaded images. Please provide clear face photos."

    db.session.commit()
    return student, None


def get_students(page=1, per_page=50, department=None, class_id=None,
                 search=None, is_active=None):
    query = Student.query
    if is_active is not None:
        query = query.filter_by(is_active=is_active)
    if department:
        query = query.filter(Student.department.ilike(f"%{department}%"))
    if class_id:
        query = query.filter_by(class_id=class_id)
    if search:
        query = query.filter(
            db.or_(
                Student.name.ilike(f"%{search}%"),
                Student.student_id.ilike(f"%{search}%"),
                Student.email.ilike(f"%{search}%"),
            )
        )
    return query.order_by(Student.name)


def get_student(student_db_id: int):
    return Student.query.get(student_db_id)


def update_student(student_db_id: int, data: dict):
    student = Student.query.get(student_db_id)
    if not student:
        return None, "Student not found."
    allowed = ["name", "phone", "department", "class_id", "roll_no", "gender", "is_active"]
    for key in allowed:
        if key in data:
            setattr(student, key, data[key])
    db.session.commit()
    return student, None


def delete_student(student_db_id: int):
    student = Student.query.get(student_db_id)
    if not student:
        return False, "Student not found."
    student.is_active = False
    db.session.commit()
    return True, None


def add_images_to_student(student_db_id: int, image_files: list):
    student = Student.query.get(student_db_id)
    if not student:
        return 0, "Student not found."

    faces_folder = os.path.join(current_app.config["FACES_FOLDER"], student.student_id)
    os.makedirs(faces_folder, exist_ok=True)
    added = 0

    for idx, img_bytes in enumerate(image_files):
        nparr = np.frombuffer(img_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is None:
            continue
        faces = detect_faces(bgr)
        if not faces:
            continue
        face_crop = crop_face(bgr, faces[0])
        filename = f"add_{uuid.uuid4().hex[:8]}.jpg"
        img_path = os.path.join(faces_folder, filename)
        cv2.imwrite(img_path, face_crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
        relative_path = f"data/faces/{student.student_id}/{filename}"

        fi = FaceImage(student_id=student.id, image_path=relative_path, angle="front")
        db.session.add(fi)

        embedding = generate_embedding_from_bgr(face_crop)
        if embedding is not None:
            er = FaceEmbedding(student_id=student.id)
            er.embedding = embedding
            db.session.add(er)
            added += 1

    db.session.commit()
    return added, None
