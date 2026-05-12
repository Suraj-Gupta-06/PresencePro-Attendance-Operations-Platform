"""
Face detection using OpenCV Haar Cascade + face_recognition HOG detector.
Provides bounding boxes, confidence, and face crops.
"""
import cv2
import numpy as np
import face_recognition
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DetectedFace:
    top: int
    right: int
    bottom: int
    left: int
    confidence: float = 1.0

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def area(self):
        return self.width * self.height

    def to_dict(self):
        return {
            "x": self.left,
            "y": self.top,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
        }


# Load Haar Cascade as lightweight fallback
_HAAR_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
_haar_cascade: Optional[cv2.CascadeClassifier] = None


def _get_haar():
    global _haar_cascade
    if _haar_cascade is None:
        _haar_cascade = cv2.CascadeClassifier(_HAAR_PATH)
    return _haar_cascade


def detect_faces_hog(rgb_image: np.ndarray) -> List[DetectedFace]:
    """
    Use face_recognition (dlib HOG) — accurate and fast on CPU.
    rgb_image: RGB numpy array
    """
    locations = face_recognition.face_locations(rgb_image, model="hog")
    faces = []
    for (top, right, bottom, left) in locations:
        faces.append(DetectedFace(top=top, right=right, bottom=bottom, left=left, confidence=0.99))
    return faces


def detect_faces_haar(bgr_image: np.ndarray) -> List[DetectedFace]:
    """
    Use OpenCV Haar Cascade — very fast, lower accuracy.
    bgr_image: BGR numpy array
    """
    cascade = _get_haar()
    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    rects = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    faces = []
    if len(rects) > 0:
        for (x, y, w, h) in rects:
            faces.append(DetectedFace(
                top=y, right=x + w, bottom=y + h, left=x, confidence=0.85
            ))
    return faces


def detect_faces(image: np.ndarray, model: str = "hog") -> List[DetectedFace]:
    """
    Detect faces in image.
    image  : BGR numpy array (from OpenCV) or RGB (detected automatically)
    model  : 'hog' (default) | 'haar'
    Returns list of DetectedFace objects sorted by area descending.
    """
    # Convert BGR → RGB for face_recognition
    if model == "haar":
        faces = detect_faces_haar(image)
    else:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        faces = detect_faces_hog(rgb)

    # Sort largest face first
    return sorted(faces, key=lambda f: f.area, reverse=True)


def crop_face(image: np.ndarray, face: DetectedFace, padding: float = 0.2) -> np.ndarray:
    """
    Crop and return the face region with optional padding.
    image : BGR numpy array
    """
    h, w = image.shape[:2]
    pad_y = int(face.height * padding)
    pad_x = int(face.width * padding)

    top = max(0, face.top - pad_y)
    bottom = min(h, face.bottom + pad_y)
    left = max(0, face.left - pad_x)
    right = min(w, face.right + pad_x)

    return image[top:bottom, left:right]


def draw_faces(image: np.ndarray, faces: List[DetectedFace],
               labels: Optional[List[str]] = None) -> np.ndarray:
    """
    Draw bounding boxes and optional labels on a copy of the image.
    """
    vis = image.copy()
    for i, face in enumerate(faces):
        color = (0, 200, 100)  # Green
        cv2.rectangle(vis, (face.left, face.top), (face.right, face.bottom), color, 2)

        label = labels[i] if labels and i < len(labels) else ""
        if label:
            # Background rectangle for text
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(vis,
                          (face.left, face.top - th - 10),
                          (face.left + tw + 6, face.top),
                          color, -1)
            cv2.putText(vis, label,
                        (face.left + 3, face.top - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    return vis
