"""
Face recognition engine.
- Generates 128-D dlib embeddings via face_recognition library
- Compares against stored DB embeddings using Euclidean distance
- Returns best match with confidence score
"""
import numpy as np
import face_recognition
import cv2
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RecognitionResult:
    matched: bool
    student_id: Optional[int]       # DB primary key
    student_code: Optional[str]     # e.g. CS2026001
    student_name: Optional[str]
    distance: float
    confidence: float               # 1 - distance (clamped 0-1)
    low_confidence: bool = False    # True if in the "uncertain" band


def generate_embedding(rgb_image: np.ndarray) -> Optional[np.ndarray]:
    """
    Generate a 128-D face embedding from an RGB image.
    Returns numpy array or None if no face found.
    """
    encodings = face_recognition.face_encodings(rgb_image)
    if encodings:
        return encodings[0]
    return None


def generate_embedding_from_bgr(bgr_image: np.ndarray) -> Optional[np.ndarray]:
    """Convenience wrapper — accepts BGR (OpenCV) image."""
    rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    return generate_embedding(rgb)


def euclidean_distance(emb1: np.ndarray, emb2: np.ndarray) -> float:
    return float(np.linalg.norm(np.array(emb1) - np.array(emb2)))


def compare_faces(known_embeddings: List[np.ndarray],
                  candidate: np.ndarray,
                  threshold: float = 0.5) -> Tuple[bool, float]:
    """
    Compare candidate embedding against a list of known embeddings.
    Returns (match_found, min_distance).
    """
    if not known_embeddings:
        return False, float("inf")

    known_arr = np.array(known_embeddings)
    # face_recognition uses Euclidean distance
    matches = face_recognition.compare_faces(known_arr, candidate, tolerance=threshold)
    distances = face_recognition.face_distance(known_arr, candidate)

    if any(matches):
        min_dist = float(np.min(distances))
        return True, min_dist
    return False, float(np.min(distances))


def recognize_face(
    candidate_embedding: np.ndarray,
    db_records: list,           # list of dicts: {student_id, student_code, name, embedding}
    threshold: float = 0.5,
    low_conf_band: float = 0.1, # distance range above threshold = "uncertain"
) -> RecognitionResult:
    """
    Match a candidate embedding against all known student embeddings.

    db_records items must have keys:
        student_id   : int
        student_code : str
        name         : str
        embedding    : list[float] (128-D)
    """
    if not db_records:
        return RecognitionResult(
            matched=False, student_id=None, student_code=None,
            student_name=None, distance=float("inf"), confidence=0.0
        )

    known_embs = [np.array(r["embedding"]) for r in db_records]
    distances = face_recognition.face_distance(known_embs, candidate_embedding)
    best_idx = int(np.argmin(distances))
    best_dist = float(distances[best_idx])

    confidence = float(max(0.0, min(1.0, 1.0 - best_dist)))

    if best_dist <= threshold:
        rec = db_records[best_idx]
        return RecognitionResult(
            matched=True,
            student_id=rec["student_id"],
            student_code=rec["student_code"],
            student_name=rec["name"],
            distance=best_dist,
            confidence=confidence,
        )
    elif best_dist <= threshold + low_conf_band:
        rec = db_records[best_idx]
        return RecognitionResult(
            matched=True,
            student_id=rec["student_id"],
            student_code=rec["student_code"],
            student_name=rec["name"],
            distance=best_dist,
            confidence=confidence,
            low_confidence=True,
        )
    else:
        return RecognitionResult(
            matched=False,
            student_id=None,
            student_code=None,
            student_name="Unknown",
            distance=best_dist,
            confidence=confidence,
        )


def average_embeddings(embeddings: List[np.ndarray]) -> np.ndarray:
    """Average multiple embeddings for more robust representation."""
    return np.mean(np.array(embeddings), axis=0)
