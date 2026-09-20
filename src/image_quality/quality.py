"""
Image quality assessment for packaged-commodity inspection.

This module performs lightweight pre-OCR checks to determine whether
an uploaded image is suitable for automated label analysis.
"""

import cv2
import numpy as np


# ------------------------------------------------------------
# Conservative thresholds
# ------------------------------------------------------------

MIN_WIDTH = 500
MIN_HEIGHT = 500

# Variance of Laplacian.
# Low values generally indicate significant blur.
BLUR_REJECT_THRESHOLD = 35.0

# Mean grayscale intensity.
BRIGHTNESS_TOO_DARK = 35.0
BRIGHTNESS_TOO_BRIGHT = 225.0

# Grayscale standard deviation.
# Very low contrast means text/background separation is poor.
CONTRAST_REJECT_THRESHOLD = 18.0


def _clamp_score(value):
    return max(0.0, min(100.0, float(value)))


def _blur_score(gray):
    """
    Estimate sharpness using variance of Laplacian.
    """
    variance = float(cv2.Laplacian(
        gray,
        cv2.CV_64F,
    ).var())

    if variance <= BLUR_REJECT_THRESHOLD:
        score = (variance / BLUR_REJECT_THRESHOLD) * 40.0
    else:
        score = 40.0 + min(
            60.0,
            (variance - BLUR_REJECT_THRESHOLD) / 4.0,
        )

    return {
        "score": round(_clamp_score(score), 1),
        "measure": round(variance, 2),
        "status": (
            "FAIL"
            if variance < BLUR_REJECT_THRESHOLD
            else "PASS"
        ),
    }


def _brightness_score(gray):
    """
    Estimate whether the image is excessively dark or bright.
    """
    brightness = float(np.mean(gray))

    if brightness < BRIGHTNESS_TOO_DARK:
        score = (
            brightness
            / BRIGHTNESS_TOO_DARK
            * 50.0
        )
        status = "FAIL"

    elif brightness > BRIGHTNESS_TOO_BRIGHT:
        score = (
            (255.0 - brightness)
            / (255.0 - BRIGHTNESS_TOO_BRIGHT)
            * 50.0
        )
        status = "FAIL"

    else:
        distance_from_middle = abs(
            brightness - 130.0
        )

        score = 100.0 - (
            distance_from_middle / 130.0 * 30.0
        )

        status = "PASS"

    return {
        "score": round(_clamp_score(score), 1),
        "measure": round(brightness, 2),
        "status": status,
    }


def _contrast_score(gray):
    """
    Estimate grayscale contrast.
    """
    contrast = float(np.std(gray))

    if contrast < CONTRAST_REJECT_THRESHOLD:
        score = (
            contrast
            / CONTRAST_REJECT_THRESHOLD
            * 50.0
        )
        status = "FAIL"
    else:
        score = 50.0 + min(
            50.0,
            (contrast - CONTRAST_REJECT_THRESHOLD)
            / 0.8,
        )
        status = "PASS"

    return {
        "score": round(_clamp_score(score), 1),
        "measure": round(contrast, 2),
        "status": status,
    }


def _resolution_score(width, height):
    """
    Estimate whether the image has enough pixels for inspection.
    """
    shortest_side = min(width, height)

    if shortest_side < MIN_WIDTH:
        score = (
            shortest_side
            / MIN_WIDTH
            * 60.0
        )
        status = "FAIL"
    else:
        score = 60.0 + min(
            40.0,
            (shortest_side - MIN_WIDTH) / 20.0,
        )
        status = "PASS"

    return {
        "score": round(_clamp_score(score), 1),
        "measure": {
            "width": width,
            "height": height,
        },
        "status": status,
    }


def assess_image_quality(image):
    """
    Assess whether an image is suitable for OCR-based inspection.

    Returns a frontend-friendly quality report.
    """

    if image is None:
        return {
            "accepted": False,
            "score": 0.0,
            "checks": {},
            "rejection_reasons": [
                "Image could not be loaded."
            ],
        }

    if len(image.shape) == 2:
        gray = image
    else:
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

    height, width = gray.shape[:2]

    checks = {
        "resolution": _resolution_score(
            width,
            height,
        ),
        "blur": _blur_score(gray),
        "brightness": _brightness_score(gray),
        "contrast": _contrast_score(gray),
    }

    rejection_reasons = []

    if checks["resolution"]["status"] == "FAIL":
        rejection_reasons.append(
            "Image resolution is too low for reliable inspection."
        )

    if checks["blur"]["status"] == "FAIL":
        rejection_reasons.append(
            "Image appears too blurry for reliable OCR."
        )

    if checks["brightness"]["status"] == "FAIL":
        rejection_reasons.append(
            "Image lighting is too dark or too bright."
        )

    if checks["contrast"]["status"] == "FAIL":
        rejection_reasons.append(
            "Image contrast is too low for reliable text detection."
        )

    # Weighted score.
    score = (
        checks["resolution"]["score"] * 0.25
        + checks["blur"]["score"] * 0.35
        + checks["brightness"]["score"] * 0.20
        + checks["contrast"]["score"] * 0.20
    )

    accepted = len(rejection_reasons) == 0

    return {
        "accepted": accepted,
        "score": round(score, 1),
        "checks": checks,
        "rejection_reasons": rejection_reasons,
    }
