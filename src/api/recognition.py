"""Face recognition API routes."""
import os
import uuid
import cv2
import numpy as np
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from src.ml.face_detection import detect_faces, crop_face
from src.ml.face_recognition_engine import generate_embedding_from_bgr, recognize_face
from src.models.embedding import FaceEmbedding
from src.models.student import Student
from src.models.system_config import SystemConfig
from src.services.attendance_service import mark_attendance, check_cooldown
from src.utils.helpers import success_response, error_response, decode_base64_image, save_cv2_image

recognition_bp = Blueprint("recognition", __name__)


def _load_all_embeddings():
    """Load all student embeddings from DB into memory for matching."""
    records = []
    embeddings_db = FaceEmbedding.query.join(Student).filter(Student.is_active == True).all()
    for emb in embeddings_db:
        student = emb.student
        records.append({
            "student_id": student.id,
            "student_code": student.student_id,
            "name": student.name,
            "embedding": emb.embedding,
        })
    return records


@recognition_bp.post("/image")
@jwt_required()
def recognize_from_image():
    """Recognize face(s) from uploaded image file."""
    if "image" not in request.files:
        return jsonify(*error_response("No image file provided."))

    file = request.files["image"]
    img_bytes = file.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if bgr is None:
        return jsonify(*error_response("Could not decode image."))

    faces = detect_faces(bgr)
    if not faces:
        return jsonify(*error_response("No face detected in image.", 400))

    threshold = float(SystemConfig.get("recognition_threshold", 0.5))
    db_records = _load_all_embeddings()
    results = []

    for face in faces[:5]:  # Process up to 5 faces
        crop = crop_face(bgr, face)
        if crop.size == 0:
            continue
        embedding = generate_embedding_from_bgr(crop)
        if embedding is None:
            continue

        result = recognize_face(embedding, db_records, threshold=threshold)
        results.append({
            "matched": result.matched,
            "student_id": result.student_id,
            "student_code": result.student_code,
            "name": result.student_name,
            "confidence": round(result.confidence, 3),
            "low_confidence": result.low_confidence,
            "bounding_box": face.to_dict(),
        })

    return jsonify(*success_response({
        "faces_detected": len(faces),
        "recognitions": results,
    }))


@recognition_bp.post("/frame")
@jwt_required()
def recognize_from_frame():
    """
    Recognize face from a base64-encoded webcam frame.
    Marks attendance automatically if recognized.
    """
    data = request.get_json(silent=True) or {}
    frame_b64 = data.get("frame")
    if not frame_b64:
        return jsonify(*error_response("No frame data provided."))

    bgr = decode_base64_image(frame_b64)
    if bgr is None:
        return jsonify(*error_response("Could not decode frame."))

    faces = detect_faces(bgr)
    if not faces:
        return jsonify(*success_response({"faces_detected": 0, "recognitions": []}))

    threshold = float(SystemConfig.get("recognition_threshold", 0.5))
    cooldown = int(SystemConfig.get("cooldown_period", 120))
    db_records = _load_all_embeddings()
    results = []

    for face in faces[:10]:
        crop = crop_face(bgr, face)
        if crop.size == 0:
            continue
        embedding = generate_embedding_from_bgr(crop)
        if embedding is None:
            continue

        result = recognize_face(embedding, db_records, threshold=threshold)

        attendance_marked = False
        already_marked = False

        if result.matched and not result.low_confidence:
            already = check_cooldown(result.student_id, cooldown)
            if not already:
                # Save frame crop
                captures_folder = current_app.config["ATTENDANCE_CAPTURES_FOLDER"]
                fname = f"{result.student_code}_{uuid.uuid4().hex[:8]}.jpg"
                img_path = save_cv2_image(crop, captures_folder, fname)
                relative = f"data/attendance_captures/{fname}"

                att, err = mark_attendance(
                    student_db_id=result.student_id,
                    confidence=result.confidence,
                    image_path=relative,
                    method="Auto",
                    cooldown_minutes=cooldown,
                )
                attendance_marked = err is None and att is not None
            else:
                already_marked = True

        results.append({
            "matched": result.matched,
            "student_id": result.student_id,
            "student_code": result.student_code,
            "name": result.student_name or "Unknown",
            "confidence": round(result.confidence, 3),
            "low_confidence": result.low_confidence,
            "attendance_marked": attendance_marked,
            "already_marked": already_marked,
            "bounding_box": face.to_dict(),
        })

    return jsonify(*success_response({
        "faces_detected": len(faces),
        "recognitions": results,
    }))
