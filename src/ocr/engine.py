"""
Common OCR engine interface.

Supported engines:
    - Tesseract
    - PaddleOCR

This module keeps the rest of the application independent
of the OCR provider.

Both engines return:

    data
    raw_text

where data is a Pandas DataFrame containing:

    text
    left
    top
    width
    height
    right
    bottom
    conf
"""

import re

import pandas as pd
import pytesseract

from .provider import create_ocr_engine


# ============================================================
# PADDLE RESULT → DATAFRAME
# ============================================================

def _paddle_result_to_dataframe(result):
    """
    Convert normalized PaddleOCR output into the DataFrame
    format expected by the existing analyzer.
    """

    rows = []

    for line in result.get("lines", []):

        text = str(
            line.get("text", "")
        ).strip()

        if not text:
            continue

        bbox = line.get("bbox")

        if not bbox or len(bbox) != 4:
            continue

        try:
            x1, y1, x2, y2 = (
                int(value)
                for value in bbox
            )

        except (TypeError, ValueError):
            continue

        try:
            confidence = float(
                line.get(
                    "confidence",
                    0.0,
                )
            )

        except (TypeError, ValueError):
            confidence = 0.0

        rows.append(
            {
                "text": text,
                "left": x1,
                "top": y1,
                "width": max(
                    0,
                    x2 - x1,
                ),
                "height": max(
                    0,
                    y2 - y1,
                ),
                "right": x2,
                "bottom": y2,
                "conf": confidence,
            }
        )

    return pd.DataFrame(
        rows,
        columns=[
            "text",
            "left",
            "top",
            "width",
            "height",
            "right",
            "bottom",
            "conf",
        ],
    )


# ============================================================
# TESSERACT
# ============================================================

def _run_tesseract(
    image,
    config,
):
    """
    Run Tesseract OCR on an OpenCV image.
    """

    data = pytesseract.image_to_data(
        image,
        config=config[
            "global_ocr_config"
        ],
        output_type=(
            pytesseract.Output.DATAFRAME
        ),
    )

    data = data.dropna(
        subset=["text"]
    )

    data["text"] = (
        data["text"]
        .astype(str)
        .str.strip()
    )

    data = data[
        data["text"] != ""
    ].copy()

    for column in (
        "left",
        "top",
        "width",
        "height",
    ):
        data[column] = (
            data[column]
            .astype(int)
        )

    data["right"] = (
        data["left"]
        + data["width"]
    )

    data["bottom"] = (
        data["top"]
        + data["height"]
    )

    raw_text = pytesseract.image_to_string(
        image,
        config=config[
            "global_ocr_config"
        ],
    )

    return data, raw_text


# ============================================================
# PADDLEOCR
# ============================================================

def _run_paddle(
    image_path,
    coordinate_scale=1.0,
):
    """
    Run PaddleOCR using the original image path.

    PaddleOCREngine returns bounding boxes in the original
    image coordinate system.

    The existing OpenCV pipeline may enlarge the image before
    region detection, so the coordinates are multiplied by
    coordinate_scale to match that processed image.
    """

    if image_path is None:
        raise ValueError(
            "image_path is required when using PaddleOCR."
        )

    engine = create_ocr_engine(
        "paddle"
    )

    result = engine.extract(
        image_path
    )

    data = _paddle_result_to_dataframe(
        result
    )

    # --------------------------------------------------------
    # Convert original-image coordinates to the coordinate
    # system used by the processed image.
    # --------------------------------------------------------

    try:
        coordinate_scale = float(
            coordinate_scale
        )

    except (
        TypeError,
        ValueError,
    ):
        coordinate_scale = 1.0

    if coordinate_scale <= 0:
        coordinate_scale = 1.0

    if coordinate_scale != 1.0 and not data.empty:

        coordinate_columns = [
            "left",
            "top",
            "width",
            "height",
            "right",
            "bottom",
        ]

        for column in coordinate_columns:

            data[column] = (
                data[column]
                * coordinate_scale
            ).round().astype(int)

    raw_text = "\n".join(
        str(line.get("text", "")).strip()
        for line in result.get(
            "lines",
            [],
        )
        if str(
            line.get("text", "")
        ).strip()
    )

    return data, raw_text


# ============================================================
# MAIN OCR FUNCTION
# ============================================================

def run_ocr(
    image,
    config,
    image_path=None,
    coordinate_scale=1.0,
):
    """
    Run the configured OCR engine.

    Parameters
    ----------
    image:
        OpenCV image used by Tesseract and kept for
        compatibility with the existing pipeline.

    config:
        Application configuration dictionary.

    image_path:
        Original image path.

        Required for PaddleOCR.

    coordinate_scale:
        Scale between the original image and the processed
        image used by region detection.

    Returns
    -------
    data:
        Pandas DataFrame containing OCR text and bounding boxes.

    raw_text:
        Complete OCR text.
    """

    engine_name = config.get(
        "ocr_engine",
        "tesseract",
    )

    engine_name = str(
        engine_name
    ).lower().strip()

    print(
        f"Running OCR engine: {engine_name}"
    )

    # --------------------------------------------------------
    # TESSERACT
    # --------------------------------------------------------

    if engine_name == "tesseract":

        data, raw_text = (
            _run_tesseract(
                image,
                config,
            )
        )

        print("OCR complete.")

        return data, raw_text

    # --------------------------------------------------------
    # PADDLEOCR
    # --------------------------------------------------------

    if engine_name == "paddle":

        data, raw_text = (
            _run_paddle(
                image_path,
                coordinate_scale,
            )
        )

        print("OCR complete.")

        return data, raw_text

    # --------------------------------------------------------
    # INVALID ENGINE
    # --------------------------------------------------------

    raise ValueError(
        f"Unsupported OCR engine: {engine_name}. "
        "Use 'tesseract' or 'paddle'."
    )


# ============================================================
# ROI OCR
# ============================================================

def ocr_roi(
    roi,
    config,
):
    """
    OCR a cropped region.

    Tesseract currently handles direct ROI OCR.

    PaddleOCR intentionally does not run here. Paddle's global
    OCR result will be reused for regions to avoid running the
    heavy model multiple times on the same image.
    """

    if roi is None:
        return ""

    from .preprocessing import (
        prepare_roi_for_ocr,
    )

    cleaned = prepare_roi_for_ocr(
        roi,
        config,
    )

    engine_name = config.get(
        "ocr_engine",
        "tesseract",
    )

    engine_name = str(
        engine_name
    ).lower().strip()

    if engine_name == "tesseract":

        return pytesseract.image_to_string(
            cleaned,
            config=config[
                "roi_ocr_config"
            ],
        )

    if engine_name == "paddle":

        raise NotImplementedError(
            "PaddleOCR ROI OCR is intentionally "
            "disabled. Use the global PaddleOCR "
            "result instead."
        )

    raise ValueError(
        f"Unsupported OCR engine: {engine_name}"
    )


# ============================================================
# OCR TEXT CLEANING
# ============================================================

def clean_word(text):
    """
    Normalize OCR words for keyword matching.
    """

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(text).lower(),
    )