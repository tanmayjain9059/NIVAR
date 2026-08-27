"""
Tesseract OCR engine utilities.
"""

import re

import pytesseract


def run_ocr(image, config):
    """
    Run Tesseract OCR and return both structured OCR data
    and complete raw text.
    """

    print("Running OCR...")

    data = pytesseract.image_to_data(
        image,
        config=config["global_ocr_config"],
        output_type=pytesseract.Output.DATAFRAME,
    )

    data = data.dropna(subset=["text"])

    data["text"] = (
        data["text"]
        .astype(str)
        .str.strip()
    )

    data = data[data["text"] != ""].copy()

    for col in ("left", "top", "width", "height"):
        data[col] = data[col].astype(int)

    data["right"] = data["left"] + data["width"]
    data["bottom"] = data["top"] + data["height"]

    text = pytesseract.image_to_string(
        image,
        config=config["global_ocr_config"],
    )

    print("OCR complete.")

    return data, text


def ocr_roi(roi, config):
    """
    Run OCR on a preprocessed region of interest.
    """

    if roi is None:
        return ""

    from .preprocessing import prepare_roi_for_ocr

    cleaned = prepare_roi_for_ocr(
        roi,
        config,
    )

    return pytesseract.image_to_string(
        cleaned,
        config=config["roi_ocr_config"],
    )


def clean_word(text):
    """
    Normalize OCR words for keyword matching.
    """

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(text).lower(),
    )
