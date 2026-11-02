"""Unit tests for anti-spoofing and liveness calculations."""
import numpy as np
from src.ml.liveness import eye_aspect_ratio, compute_sharpness


def test_eye_aspect_ratio_open_eye():
    """Test EAR calculation for synthetic open eye coordinates."""
    # 6 points representing an open eye
    p1 = (30, 50)
    p2 = (35, 40)
    p3 = (45, 40)
    p4 = (50, 50)
    p5 = (45, 60)
    p6 = (35, 60)
    eye = [p1, p2, p3, p4, p5, p6]

    ear = eye_aspect_ratio(eye)
    assert 0.20 <= ear <= 1.5


def test_eye_aspect_ratio_closed_eye():
    """Test EAR calculation for nearly closed eye points."""
    p1 = (30, 50)
    p2 = (35, 49)
    p3 = (45, 49)
    p4 = (50, 50)
    p5 = (45, 51)
    p6 = (35, 51)
    eye = [p1, p2, p3, p4, p5, p6]

    ear = eye_aspect_ratio(eye)
    assert ear < 0.15


def test_compute_sharpness_uniform_image():
    """Test that a flat, featureless image has near-zero sharpness (blur/spoof indicator)."""
    flat_image = np.ones((100, 100, 3), dtype=np.uint8) * 128
    score = compute_sharpness(flat_image)
    assert score < 5.0
