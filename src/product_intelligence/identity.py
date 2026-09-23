"""
Robust product/brand identity extraction from OCR.

The extractor prefers explicit semantic labels, then falls back to
high-confidence layout candidates. It deliberately rejects common
nutrition, compliance, contact, address, and metadata text.
"""

import re
from typing import Any


PRODUCT_LABEL_RE = re.compile(
    r"\b(?:product\s*name|name\s*of\s*product|product)\b"
    r"\s*[:\-]?\s*(.+)",
    re.IGNORECASE,
)

BRAND_LABEL_RE = re.compile(
    r"\bbrand\b\s*[:\-]?\s*(.+)",
    re.IGNORECASE,
)

MANUFACTURER_BRAND_RE = re.compile(
    r"\b(?:manufactured|marketed|packed|imported)\s+by\b"
    r"\s*[:\-]?\s*(.+)",
    re.IGNORECASE,
)

NOISE_RE = re.compile(
    r"\b(?:mrp|m\.r\.p|net\s*(?:qty|quantity|weight)|"
    r"ingredients?|nutrition(?:al)?(?:\s+information)?|"
    r"energy|protein|carbohydrate|sugars?|fat|fiber|"
    r"sodium|cholesterol|saturated|trans\s+fat|"
    r"manufactured|packed|marketed|imported|"
    r"customer\s+care|consumer\s+care|"
    r"batch|lot|pkd|mfd|mfg|barcode|"
    r"use\s*by|best\s*before|expiry|"
    r"country\s+of\s+origin|contains|may\s+contain|"
    r"keep\s+in|store\s+in|directions|warning|"
    r"license|licence|fssai|www\.|@)\b",
    re.IGNORECASE,
)

COMPANY_SUFFIX_RE = re.compile(
    r"\b(?:private\s+limited|pvt\.?\s*ltd\.?|limited|ltd\.?|"
    r"foods?|industr(?:y|ies)|corporation|corp\.?|"
    r"enterprises?|industries|llp)\b.*$",
    re.IGNORECASE,
)

NUTRITION_CONTEXT_RE = re.compile(
    r"\b(?:nutrition|nutritional|energy|protein|carbohydrate|"
    r"sugar|fat|fiber|sodium|cholesterol|kcal|rda)\b",
    re.IGNORECASE,
)


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _confidence(value: Any) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    if value > 1:
        value /= 100.0
    return max(0.0, min(value, 1.0))


def _bbox(row) -> dict[str, int] | None:
    try:
        return {
            "x1": int(float(row["left"])),
            "y1": int(float(row["top"])),
            "x2": int(float(row["right"])),
            "y2": int(float(row["bottom"])),
        }
    except (KeyError, TypeError, ValueError):
        return None


def _evidence(row, text: str | None = None) -> dict[str, Any] | None:
    box = _bbox(row)
    if box is None:
        return None
    return {
        "text": _clean(text if text is not None else row.get("text")),
        "confidence": _confidence(row.get("conf", 0)),
        "bbox": box,
    }


def _looks_like_noise(text: str, raw_text: str = "") -> bool:
    text = _clean(text)
    if len(text) < 2 or len(text) > 100:
        return True
    if re.fullmatch(r"[\d\s./:%₹$€£+\-]+", text):
        return True
    if NOISE_RE.search(text):
        return True
    if sum(c.isalpha() for c in text) < 2:
        return True
    if len(re.findall(r"\d", text)) > max(3, len(text) // 3):
        return True
    return False


def _clean_product_candidate(value: str) -> str:
    value = _clean(value)
    value = re.split(
        r"\b(?:mrp|net\s*(?:qty|quantity)|ingredients?|nutrition|"
        r"contains|may\s+contain|manufactured\s+by|marketed\s+by|"
        r"packed\s+by|customer\s+care)\b",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return value.strip(" :-.,;")


def _clean_brand_candidate(value: str) -> str:
    value = _clean(value)
    value = re.split(
        r"\b(?:fssai|license|licence|manufactured|marketed|packed|"
        r"imported|address|customer\s+care|consumer\s+care|"
        r"www\.|@|phone|tel)\b",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    value = value.strip(" :-.,;")
    value = COMPANY_SUFFIX_RE.sub("", value).strip(" :-.,;")
    return value


def _explicit_candidates(ocr_data):
    if ocr_data is None or getattr(ocr_data, "empty", True):
        return [], []

    products = []
    brands = []

    for _, row in ocr_data.iterrows():
        text = _clean(row.get("text"))
        if not text:
            continue

        match = PRODUCT_LABEL_RE.search(text)
        if match:
            candidate = _clean_product_candidate(match.group(1))
            if candidate and not _looks_like_noise(candidate):
                ev = _evidence(row, text)
                if ev:
                    products.append({
                        "value": candidate,
                        "confidence": ev["confidence"],
                        "evidence": ev,
                        "source": "explicit_product_label",
                    })

        match = BRAND_LABEL_RE.search(text)
        if match:
            candidate = _clean_brand_candidate(match.group(1))
            if candidate and not _looks_like_noise(candidate):
                ev = _evidence(row, text)
                if ev:
                    brands.append({
                        "value": candidate,
                        "confidence": ev["confidence"],
                        "evidence": ev,
                        "source": "explicit_brand_label",
                    })

        match = MANUFACTURER_BRAND_RE.search(text)
        if match:
            candidate = _clean_brand_candidate(match.group(1))
            if candidate and not _looks_like_noise(candidate):
                ev = _evidence(row, text)
                if ev:
                    brands.append({
                        "value": candidate,
                        "confidence": min(ev["confidence"], 0.90),
                        "evidence": ev,
                        "source": "manufacturer_label",
                    })

    return products, brands


def _layout_candidates(ocr_data, raw_text: str):
    if ocr_data is None or getattr(ocr_data, "empty", True):
        return []

    try:
        image_width = max(float(ocr_data["right"].max()), 1.0)
        image_height = max(float(ocr_data["bottom"].max()), 1.0)
    except (KeyError, TypeError, ValueError):
        image_width = image_height = 1.0

    candidates = []

    for _, row in ocr_data.iterrows():
        text = _clean(row.get("text"))
        if _looks_like_noise(text, raw_text):
            continue

        try:
            left = float(row["left"])
            top = float(row["top"])
            right = float(row["right"])
            bottom = float(row["bottom"])
        except (KeyError, TypeError, ValueError):
            continue

        confidence = _confidence(row.get("conf", 0))
        width = max(1.0, right - left)
        height = max(1.0, bottom - top)
        area_ratio = width * height / (image_width * image_height)

        score = confidence * 55
        score += min(area_ratio * 12000, 25)
        if top / image_height < 0.45:
            score += 12
        if 2 <= len(text.split()) <= 8:
            score += 6
        if len(text) >= 4:
            score += 4

        if NUTRITION_CONTEXT_RE.search(text):
            score -= 35

        ev = _evidence(row)
        if ev:
            candidates.append({
                "value": text,
                "score": round(score, 3),
                "confidence": confidence,
                "evidence": ev,
                "source": "layout_candidate",
            })

    return sorted(candidates, key=lambda x: x["score"], reverse=True)


def identify_product(raw_text: str, ocr_data=None) -> dict[str, Any]:
    """
    Identify product and brand while preserving OCR evidence.

    Priority:
      1. Explicit Product/Brand labels
      2. Manufacturer/marketed-by brand evidence
      3. High-confidence visual/layout candidate

    Generic nutrition/compliance/contact text is intentionally rejected.
    """
    explicit_products, explicit_brands = _explicit_candidates(ocr_data)
    layout = _layout_candidates(ocr_data, raw_text or "")

    selected_product = explicit_products[0] if explicit_products else (
        layout[0] if layout else None
    )
    selected_brand = explicit_brands[0] if explicit_brands else None

    return {
        "product_name": selected_product["value"] if selected_product else None,
        "product_name_confidence": (
            selected_product["confidence"] if selected_product else None
        ),
        "product_name_evidence": (
            selected_product["evidence"] if selected_product else None
        ),
        "brand": selected_brand["value"] if selected_brand else None,
        "brand_confidence": (
            selected_brand["confidence"] if selected_brand else None
        ),
        "brand_evidence": (
            selected_brand["evidence"] if selected_brand else None
        ),
        "product_name_candidates": (
            explicit_products[:5] or layout[:5]
        ),
        "brand_candidates": explicit_brands[:5],
    }
