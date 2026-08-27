"""
Image preprocessing utilities for food-label OCR.
"""

import cv2


def normalize_polarity(gray, config):
    """
    Invert predominantly dark images so Tesseract sees
    dark text on a light background.
    """

    if gray.mean() < config["polarity_dark_threshold"]:
        print("Detected dark-background label — inverting for OCR.")
        return cv2.bitwise_not(gray)

    return gray


def preprocess_image(image, config):
    """
    Resize and enhance the image before OCR.

    Returns:
        enlarged: resized BGR image
        enhanced: grayscale/contrast-enhanced image
    """

    scale = config["scale"]

    enlarged = cv2.resize(
        image,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC,
    )

    print(f"Image enlarged by {scale}x")

    gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    enhanced = clahe.apply(gray)

    print("Contrast enhancement complete.")

    enhanced = normalize_polarity(enhanced, config)

    return enlarged, enhanced


def prepare_roi_for_ocr(roi, config):
    """
    Prepare a cropped region for OCR using denoising
    and Otsu binarization.
    """

    if roi is None:
        return None

    denoised = cv2.medianBlur(
        roi,
        config["roi_denoise_kernel"],
    )

    _, binarized = cv2.threshold(
        denoised,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    return binarized
