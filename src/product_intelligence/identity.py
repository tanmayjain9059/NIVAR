"""
Robust product/brand identity extraction from OCR.

Semantic labels are preferred over layout guesses. The extractor rejects
legal-metrology, nutrition, contact, address, license, and barcode text.
"""

import re
from typing import Any


PRODUCT_LABEL_RE = re.compile(
    r"\b(?:product\s*name|name\s*of\s*product)\b\s*[:\-]?\s*(.+)",
    re.IGNORECASE,
)
BRAND_LABEL_RE = re.compile(r"\bbrand\b\s*[:\-]?\s*(.+)", re.IGNORECASE)
MANUFACTURER_BRAND_RE = re.compile(
    r"\b(?:manufactured|marketed|packed|imported)\s+by\b\s*[:\-]?\s*(.+)",
    re.IGNORECASE,
)

NOISE_RE = re.compile(
    r"\b(?:mrp|m\.r\.p|net\s*(?:qty|quantity|weight)|ingredients?|"
    r"nutrition(?:al)?|energy|protein|carbohydrate|sugars?|fat|fiber|"
    r"sodium|cholesterol|saturated|trans\s*fat|batch|lot|pkd|mfd|mfg|"
    r"barcode|use\s*by|best\s*before|expiry|country\s+of\s+origin|"
    r"contains|may\s+contain|keep\s+in|store\s+in|directions|warning|"
    r"license|licence|fssai|customer\s+care|consumer\s+care|"
    r"manufactured|packed|marketed|imported|www\.|@)\b",
    re.IGNORECASE,
)

COMPANY_SUFFIX_RE = re.compile(
    r"\b(?:private\s+limited|pvt\.?\s*ltd\.?|limited|ltd\.?|"
    r"foods?|industr(?:y|ies)|corporation|corp\.?|enterprises?|llp)\b.*$",
    re.IGNORECASE,
)
NUTRITION_CONTEXT_RE = re.compile(
    r"\b(?:nutrition|nutritional|energy|protein|carbohydrate|sugar|fat|"
    r"fiber|sodium|cholesterol|kcal|rda)\b",
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


def _valid_candidate(text: str) -> bool:
    text = _clean(text)
    if not 2 <= len(text) <= 100:
        return False
    if re.fullmatch(r"[\d\s./:%₹$€£+\-]+", text):
        return False
    if NOISE_RE.search(text):
        return False
    if sum(c.isalpha() for c in text) < 2:
        return False
    if len(re.findall(r"\d", text)) > max(3, len(text) // 3):
        return False
    return True


def _clean_product_candidate(value: str) -> str:
    value = _clean(value)
    value = re.split(
        r"\b(?:mrp|net\s*(?:qty|quantity)|ingredients?|nutrition|contains|"
        r"may\s+contain|manufactured\s+by|marketed\s+by|packed\s+by|"
        r"customer\s+care)\b",
        value, maxsplit=1, flags=re.IGNORECASE,
    )[0]
    return value.strip(" :-.,;")


def _clean_brand_candidate(value: str) -> str:
    value = _clean(value)
    value = re.split(
        r"\b(?:fssai|license|licence|manufactured|marketed|packed|imported|"
        r"address|customer\s+care|consumer\s+care|www\.|@|phone|tel|"
        r"contact)\b",
        value, maxsplit=1, flags=re.IGNORECASE,
    )[0]
    value = value.strip(" :-.,;")
    value = COMPANY_SUFFIX_RE.sub("", value).strip(" :-.,;")
    return value


def _explicit_candidates(ocr_data):
    if ocr_data is None or getattr(ocr_data, "empty", True):
        return [], []
    products, brands = [], []
    for _, row in ocr_data.iterrows():
        text = _clean(row.get("text"))
        if not text:
            continue
        match = PRODUCT_LABEL_RE.search(text)
        if match:
            candidate = _clean_product_candidate(match.group(1))
            if _valid_candidate(candidate):
                ev = _evidence(row, text)
                if ev:
                    products.append({
                        "value": candidate, "confidence": ev["confidence"],
                        "evidence": ev, "source": "explicit_product_label",
                    })
        match = BRAND_LABEL_RE.search(text)
        if match:
            candidate = _clean_brand_candidate(match.group(1))
            if _valid_candidate(candidate):
                ev = _evidence(row, text)
                if ev:
                    brands.append({
                        "value": candidate, "confidence": ev["confidence"],
                        "evidence": ev, "source": "explicit_brand_label",
                    })
        match = MANUFACTURER_BRAND_RE.search(text)
        if match:
            candidate = _clean_brand_candidate(match.group(1))
            if _valid_candidate(candidate):
                ev = _evidence(row, text)
                if ev:
                    brands.append({
                        "value": candidate, "confidence": min(ev["confidence"], 0.90),
                        "evidence": ev, "source": "manufacturer_label",
                    })
    return products, brands


def _layout_candidates(ocr_data):
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
        if not _valid_candidate(text):
            continue
        try:
            left, top = float(row["left"]), float(row["top"])
            right, bottom = float(row["right"]), float(row["bottom"])
        except (KeyError, TypeError, ValueError):
            continue
        confidence = _confidence(row.get("conf", 0))
        area_ratio = max(1.0, right-left) * max(1.0, bottom-top) / (image_width * image_height)
        score = confidence * 55 + min(area_ratio * 12000, 25)
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
                "value": text, "score": round(score, 3), "confidence": confidence,
                "evidence": ev, "source": "layout_candidate",
            })
    return sorted(candidates, key=lambda item: item["score"], reverse=True)


def identify_product(raw_text: str, ocr_data=None) -> dict[str, Any]:
    explicit_products, explicit_brands = _explicit_candidates(ocr_data)
    layout = _layout_candidates(ocr_data)
    selected_product = explicit_products[0] if explicit_products else (layout[0] if layout else None)
    selected_brand = explicit_brands[0] if explicit_brands else None
    return {
        "product_name": selected_product["value"] if selected_product else None,
        "product_name_confidence": selected_product["confidence"] if selected_product else None,
        "product_name_evidence": selected_product["evidence"] if selected_product else None,
        "brand": selected_brand["value"] if selected_brand else None,
        "brand_confidence": selected_brand["confidence"] if selected_brand else None,
        "brand_evidence": selected_brand["evidence"] if selected_brand else None,
        "product_name_candidates": explicit_products[:5] or layout[:5],
        "brand_candidates": explicit_brands[:5],
    }
