"""
Product identity extraction.

This module identifies likely product name and brand candidates
from OCR text and OCR geometry.

The implementation is deterministic and preserves evidence
for every selected identity value.
"""

import re
from typing import Any


BRAND_LABEL_PATTERN = re.compile(
    r"\b(?:brand|manufactured\s+by|marketed\s+by)\b",
    re.IGNORECASE,
)


PRODUCT_LABEL_PATTERN = re.compile(
    r"\b(?:product\s+name|name\s+of\s+product|product)\b"
    r"\s*[:\-]?\s*(.+)",
    re.IGNORECASE,
)


NOISE_PATTERN = re.compile(
    r"^(?:"
    r"mrp|m\.r\.p|"
    r"net\s*(?:qty|quantity|weight)|"
    r"ingredients?|"
    r"nutrition|"
    r"manufactured|"
    r"manufactured\s+by|"
    r"packed\s+by|"
    r"marketed\s+by|"
    r"customer\s+care|"
    r"consumer\s+care|"
    r"batch|"
    r"lot|"
    r"pkd|"
    r"mfd|"
    r"mfg|"
    r"use\s*by|"
    r"best\s*before|"
    r"barcode|"
    r"country\s+of\s+origin"
    r")\b",
    re.IGNORECASE,
)


NUMERIC_HEAVY_PATTERN = re.compile(
    r"^[\d\s./:%₹$€£\-]+$"
)


def _clean_text(
    value: Any,
) -> str:
    """
    Normalize OCR text for identity processing.
    """

    text = str(
        value or ""
    ).strip()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def _normalize_confidence(
    value: Any,
) -> float:
    """
    Normalize OCR confidence to the 0.0–1.0 range.

    Paddle-style confidence is typically already 0–1.

    Tesseract confidence may be 0–100.
    """

    try:
        confidence = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0.0

    if confidence < 0:
        return 0.0

    if confidence > 1.0:
        confidence /= 100.0

    return max(
        0.0,
        min(
            confidence,
            1.0,
        ),
    )


def _looks_like_noise(
    text: str,
) -> bool:
    """
    Determine whether OCR text is unsuitable as identity text.
    """

    if not text:
        return True

    if len(text) < 2:
        return True

    if NUMERIC_HEAVY_PATTERN.fullmatch(
        text
    ):
        return True

    if NOISE_PATTERN.search(
        text
    ):
        return True

    return False


def _bbox_area(
    row,
) -> float:
    """
    Calculate OCR bounding-box area.
    """

    try:
        width = max(
            0.0,
            float(row["right"])
            - float(row["left"]),
        )

        height = max(
            0.0,
            float(row["bottom"])
            - float(row["top"]),
        )

        return width * height

    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        return 0.0


def _candidate_score(
    row,
    image_width: float,
    image_height: float,
) -> float:
    """
    Score a generic OCR line as a possible product name.
    """

    text = _clean_text(
        row.get("text")
    )

    confidence = _normalize_confidence(
        row.get("conf", 0.0)
    )

    area = _bbox_area(
        row
    )

    image_area = max(
        1.0,
        image_width * image_height,
    )

    area_ratio = (
        area / image_area
    )

    try:
        top = float(
            row["top"]
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        top = 0.0

    vertical_position = (
        top
        / max(
            1.0,
            image_height,
        )
    )

    alphabetic_count = sum(
        character.isalpha()
        for character in text
    )

    digit_count = sum(
        character.isdigit()
        for character in text
    )

    score = (
        confidence * 50.0
    )

    score += min(
        area_ratio * 10000.0,
        25.0,
    )

    if vertical_position <= 0.45:
        score += 15.0

    if alphabetic_count >= 3:
        score += 10.0

    if digit_count == 0:
        score += 5.0

    if 2 <= len(
        text.split()
    ) <= 8:
        score += 5.0

    return score


def _evidence_from_row(
    row,
) -> dict[str, Any] | None:
    """
    Create structured evidence from one OCR row.
    """

    try:
        bbox = {
            "x1": int(
                float(row["left"])
            ),
            "y1": int(
                float(row["top"])
            ),
            "x2": int(
                float(row["right"])
            ),
            "y2": int(
                float(row["bottom"])
            ),
        }

    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        return None

    return {
        "text": _clean_text(
            row.get("text")
        ),
        "confidence": _normalize_confidence(
            row.get("conf", 0.0)
        ),
        "bbox": bbox,
    }


def _extract_product_value(
    text: str,
) -> str:
    """
    Extract only the value portion from an explicit product label.

    Handles examples such as:

        Product: Premium Rice
        Product Name: Premium Rice
        Name of Product: Premium Rice

    without accidentally returning the label itself.
    """

    match = PRODUCT_LABEL_PATTERN.search(
        text
    )

    if not match:
        return ""

    candidate = _clean_text(
        match.group(1)
    )

    return candidate


def _extract_brand_value(
    text: str,
) -> str:
    """
    Extract the value portion from an explicit brand/manufacturer
    style label.
    """

    match = re.search(
        r"\b(?:brand|manufactured\s+by|marketed\s+by)\b"
        r"\s*[:\-]?\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if not match:
        return ""

    return _clean_text(
        match.group(1)
    )


def _explicit_product_candidate(
    ocr_data,
) -> dict[str, Any] | None:
    """
    Find an explicitly labelled product-name candidate.
    """

    if (
        ocr_data is None
        or getattr(
            ocr_data,
            "empty",
            True,
        )
    ):
        return None

    for _, row in ocr_data.iterrows():

        text = _clean_text(
            row.get("text")
        )

        candidate = _extract_product_value(
            text
        )

        if _looks_like_noise(
            candidate
        ):
            continue

        if not candidate:
            continue

        evidence = _evidence_from_row(
            row
        )

        if evidence is None:
            continue

        return {
            "value": candidate,
            "confidence": evidence[
                "confidence"
            ],
            "evidence": evidence,
            "source": "explicit_product_label",
        }

    return None


def _explicit_brand_candidate(
    ocr_data,
) -> dict[str, Any] | None:
    """
    Find an explicitly labelled brand candidate.
    """

    if (
        ocr_data is None
        or getattr(
            ocr_data,
            "empty",
            True,
        )
    ):
        return None

    for _, row in ocr_data.iterrows():

        text = _clean_text(
            row.get("text")
        )

        if not BRAND_LABEL_PATTERN.search(
            text
        ):
            continue

        candidate = _extract_brand_value(
            text
        )

        if _looks_like_noise(
            candidate
        ):
            continue

        if not candidate:
            continue

        evidence = _evidence_from_row(
            row
        )

        if evidence is None:
            continue

        return {
            "value": candidate,
            "confidence": evidence[
                "confidence"
            ],
            "evidence": evidence,
            "source": "explicit_brand_label",
        }

    return None


def identify_product(
    raw_text: str,
    ocr_data=None,
) -> dict[str, Any]:
    """
    Identify product name and brand from OCR output.

    Explicitly labelled fields take precedence over layout-based
    candidates.

    Evidence is preserved with:

        text
        confidence
        bounding box
    """

    explicit_product = (
        _explicit_product_candidate(
            ocr_data
        )
    )

    explicit_brand = (
        _explicit_brand_candidate(
            ocr_data
        )
    )

    product_candidates = []

    if (
        ocr_data is not None
        and not getattr(
            ocr_data,
            "empty",
            True,
        )
    ):

        try:
            image_width = max(
                float(
                    ocr_data[
                        "right"
                    ].max()
                ),
                1.0,
            )

            image_height = max(
                float(
                    ocr_data[
                        "bottom"
                    ].max()
                ),
                1.0,
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            image_width = 1.0
            image_height = 1.0

        for _, row in ocr_data.iterrows():

            text = _clean_text(
                row.get("text")
            )

            if _looks_like_noise(
                text
            ):
                continue

            score = _candidate_score(
                row,
                image_width,
                image_height,
            )

            evidence = _evidence_from_row(
                row
            )

            if evidence is None:
                continue

            product_candidates.append(
                {
                    "value": text,
                    "score": round(
                        score,
                        3,
                    ),
                    "confidence": evidence[
                        "confidence"
                    ],
                    "evidence": evidence,
                    "source": "layout_candidate",
                }
            )

    product_candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    selected_product = (
        explicit_product
        or (
            product_candidates[0]
            if product_candidates
            else None
        )
    )

    selected_brand = (
        explicit_brand
    )

    return {
        "product_name": (
            selected_product["value"]
            if selected_product
            else None
        ),

        "product_name_confidence": (
            selected_product[
                "confidence"
            ]
            if selected_product
            else None
        ),

        "product_name_evidence": (
            selected_product[
                "evidence"
            ]
            if selected_product
            else None
        ),

        "brand": (
            selected_brand["value"]
            if selected_brand
            else None
        ),

        "brand_confidence": (
            selected_brand[
                "confidence"
            ]
            if selected_brand
            else None
        ),

        "brand_evidence": (
            selected_brand[
                "evidence"
            ]
            if selected_brand
            else None
        ),

        "product_name_candidates": (
            product_candidates[:5]
        ),
    }