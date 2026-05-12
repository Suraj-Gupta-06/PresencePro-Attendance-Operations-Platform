"""
Image preprocessor — quality checks, face alignment, resizing.
"""
import cv2
import numpy as np
from PIL import Image


def check_image_quality(image: np.ndarray) -> dict:
    """
    Returns a dict with quality metrics and a pass/fail flag.
    image: BGR numpy array
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Brightness (mean pixel value 0-255)
    brightness = float(np.mean(gray))

    # Sharpness via Laplacian variance
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    passed = brightness >= 40 and sharpness >= 50

    return {
        "brightness": round(brightness, 2),
        "sharpness": round(sharpness, 2),
        "passed": passed,
        "reason": None if passed else (
            "Too dark" if brightness < 40 else "Too blurry"
        ),
    }


def resize_and_pad(image: np.ndarray, target_size: int = 160) -> np.ndarray:
    """Resize image keeping aspect ratio and pad to square."""
    h, w = image.shape[:2]
    scale = target_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(image, (new_w, new_h))

    # Pad to square
    top = (target_size - new_h) // 2
    bottom = target_size - new_h - top
    left = (target_size - new_w) // 2
    right = target_size - new_w - left
    padded = cv2.copyMakeBorder(resized, top, bottom, left, right,
                                cv2.BORDER_CONSTANT, value=(0, 0, 0))
    return padded


def preprocess_for_recognition(face_bgr: np.ndarray) -> np.ndarray:
    """Convert BGR face crop → RGB, resize to 160×160."""
    face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
    face_rgb = cv2.resize(face_rgb, (160, 160))
    return face_rgb


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    """Decode image bytes (from file upload) to BGR numpy array."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """Convert PIL RGB image to OpenCV BGR."""
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)


def cv2_to_pil(bgr: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR to PIL RGB."""
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
