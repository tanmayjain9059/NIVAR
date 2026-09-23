"""Product and brand identity extraction for packaged-food labels."""

import re
from typing import Any

PRODUCT_LABEL_RE = re.compile(
    r"\b(?:product\s*name|name\s*of\s*product|name\s*of\s*food)\b\s*[:\-]?\s*(.+)",
    re.I,
)
BRAND_LABEL_RE = re.compile(r"\bbrand\b\s*[:\-]?\s*(.+)", re.I)
MANUFACTURER_RE = re.compile(
    r"\b(?:manufactured|marketed|packed|imported)\s+by\b\s*[:\-]?\s*(.+)",
    re.I,
)

NOISE_RE = re.compile(
    r"\b(?:mrp|m\.r\.p|net\s*(?:qty|quantity|weight)|ingredients?|nutrition(?:al)?|"
    r"energy|protein|carbohydrate|sugars?|fat|fiber|sodium|cholesterol|saturated|"
    r"trans\s*fat|batch|lot|pkd|mfd|mfg|barcode|use\s*by|best\s*before|expiry|"
    r"country\s+of\s+origin|contains|may\s+contain|keep\s+in|store\s+in|"
    r"directions|warning|license|licence|fssai|customer\s+care|consumer\s+care|"
    r"manufactured|packed|marketed|imported|www\.|@)\b",
    re.I,
)

NUTRITION_RE = re.compile(
    r"\b(?:nutrition|nutritional|energy|protein|carbohydrate|sugar|fat|fiber|"
    r"sodium|cholesterol|kcal|rda)\b",
    re.I,
)

COMPANY_RE = re.compile(
    r"\b(?:pvt\.?\s*ltd\.?|private\s+limited|ltd\.?|limited|llp|inc\.?|"
    r"incorporated|corp\.?|corporation|co\.?|company|industries|foods|"
    r"food\s+products|enterprises|traders|manufacturers?)\b",
    re.I,
)

ADDRESS_RE = re.compile(
    r"\b(?:plot|road|street|lane|avenue|industrial\s+area|estate|sector|block|"
    r"district|taluka|tehsil|village|nagar|colony|pin(?:code)?|postcode|zip|"
    r"near|opposite|opp\.?|phase|highway|city|state)\b",
    re.I,
)

FOOD_TYPE_RE = re.compile(
    r"\b(?:rice|basmati|flour|atta|maida|suji|sooji|dal|lentil|pulses?|wheat|"
    r"oats?|poha|flattened\s+rice|noodles?|pasta|biscuit(?:s)?|cookies?|bread|"
    r"rusk|namkeen|snack(?:s)?|chips?|mixture|cereal(?:s)?|corn(?:flakes)?|"
    r"muesli|chocolate|cocoa|tea|coffee|juice|drink|beverage|milk|curd|yogurt|"
    r"ghee|butter|cheese|oil|pickle|jam|sauce|ketchup|spice(?:s)?|masala|salt|"
    r"sugar|honey|jaggery|vermicelli|semolina|gram|chana|rajma|peas?|nuts?|"
    r"almonds?|cashews?|seasoning|powder|mix|blend|paste)\b",
    re.I,
)

MARKETING_RE = re.compile(
    r"\b(?:everyone|gathered|moments|warmth|finest|first\s+bite|last\s+crumb|"
    r"heaven|sharing|loved\s+ones|discover|range|baked|buttery|meant\s+for)\b",
    re.I,
)


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _confidence(value: Any) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    if value > 1:
        value /= 100
    return max(0.0, min(value, 1.0))


def _bbox(row):
    try:
        return {
            "x1": int(float(row["left"])),
            "y1": int(float(row["top"])),
            "x2": int(float(row["right"])),
            "y2": int(float(row["bottom"])),
        }
    except (KeyError, TypeError, ValueError):
        return None


def _evidence(row, text=None):
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
    if not 2 <= len(text) <= 80:
        return False
    if re.fullmatch(r"[\d\s./:%₹$€£+\-]+", text):
        return False
    if NOISE_RE.search(text):
        return False
    if COMPANY_RE.search(text) or ADDRESS_RE.search(text):
        return False
    if sum(c.isalpha() for c in text) < 2:
        return False
    if len(text.split()) > 8:
        return False
    return True


def _clean_candidate(value: str) -> str:
    value = _clean(value)
    value = re.split(
        r"\b(?:mrp|net\s*(?:qty|quantity)|ingredients?|nutrition|contains|"
        r"may\s+contain|manufactured\s+by|marketed\s+by|packed\s+by|"
        r"customer\s+care)\b",
        value,
        maxsplit=1,
        flags=re.I,
    )[0]
    return value.strip(" :-.,;")


def _candidate_score(value: str, confidence: float = 0.5, front=False) -> float:
    score = confidence * 50
    words = len(value.split())

    if FOOD_TYPE_RE.search(value):
        score += 40
    else:
        return -999

    if 2 <= words <= 5:
        score += 12
    elif words > 6:
        score -= 12

    if 4 <= len(value) <= 55:
        score += 5

    if front:
        score += 15

    if MARKETING_RE.search(value):
        score -= 35

    if NUTRITION_RE.search(value):
        score -= 60

    if any(ch in value for ch in ".!?"):
        score -= 25

    return score


def _explicit_candidates(ocr_data):
    products = []
    brands = []

    if ocr_data is None or getattr(ocr_data, "empty", True):
        return products, brands

    for _, row in ocr_data.iterrows():
        text = _clean(row.get("text"))
        if not text:
            continue

        match = PRODUCT_LABEL_RE.search(text)
        if match:
            value = _clean_candidate(match.group(1))
            if _valid_candidate(value):
                evidence = _evidence(row, text)
                if evidence:
                    products.append({
                        "value": value,
                        "confidence": evidence["confidence"],
                        "score": evidence["confidence"] * 100 + 100,
                        "evidence": evidence,
                        "source": "explicit_product_label",
                    })

        match = BRAND_LABEL_RE.search(text)
        if match:
            value = _clean_candidate(match.group(1))
            if _valid_candidate(value):
                evidence = _evidence(row, text)
                if evidence:
                    brands.append({
                        "value": value,
                        "confidence": evidence["confidence"],
                        "evidence": evidence,
                        "source": "explicit_brand_label",
                    })

        match = MANUFACTURER_RE.search(text)
        if match:
            value = _clean_candidate(match.group(1))
            if _valid_candidate(value):
                evidence = _evidence(row, text)
                if evidence:
                    brands.append({
                        "value": value,
                        "confidence": min(evidence["confidence"], 0.9),
                        "evidence": evidence,
                        "source": "manufacturer_label",
                    })

    return products, brands


def _front_candidates(ocr_data):
    if ocr_data is None or getattr(ocr_data, "empty", True):
        return []

    try:
        image_height = max(float(ocr_data["bottom"].max()), 1.0)
    except (KeyError, TypeError, ValueError):
        return []

    rows = []
    for _, row in ocr_data.iterrows():
        text = _clean(row.get("text"))
        if not text or not _valid_candidate(text):
            continue

        try:
            top = float(row["top"])
            confidence = _confidence(row.get("conf", 0))
        except (KeyError, TypeError, ValueError):
            continue

        if top / image_height > 0.55:
            continue

        score = _candidate_score(
            text,
            confidence,
            front=top / image_height < 0.40,
        )

        if score < 35:
            continue

        evidence = _evidence(row)
        if evidence:
            rows.append({
                "value": text,
                "score": round(score, 3),
                "confidence": confidence,
                "evidence": evidence,
                "source": "front_panel_candidate",
                "row": row,
            })

    return rows


def _joined_candidates(ocr_data):
    if ocr_data is None or getattr(ocr_data, "empty", True):
        return []

    rows = []
    try:
        image_height = max(float(ocr_data["bottom"].max()), 1.0)
    except (KeyError, TypeError, ValueError):
        return []

    for _, row in ocr_data.iterrows():
        text = _clean(row.get("text"))
        if not text:
            continue
        try:
            rows.append({
                "text": text,
                "left": float(row["left"]),
                "top": float(row["top"]),
                "right": float(row["right"]),
                "bottom": float(row["bottom"]),
                "confidence": _confidence(row.get("conf", 0)),
                "row": row,
            })
        except (KeyError, TypeError, ValueError):
            continue

    rows = [
        row for row in rows
        if row["top"] / image_height < 0.55
        and _valid_candidate(row["text"])
    ]

    candidates = []

    for left in rows:
        for right in rows:
            if right is left:
                continue
            if right["left"] < left["left"]:
                continue

            same_line = abs(
                ((left["top"] + left["bottom"]) / 2)
                - ((right["top"] + right["bottom"]) / 2)
            ) <= max(
                left["bottom"] - left["top"],
                right["bottom"] - right["top"],
                20,
            )

            close = right["left"] - left["right"] <= 6 * max(
                left["bottom"] - left["top"], 20
            )

            if not same_line or not close:
                continue

            value = _clean(f'{left["text"]} {right["text"]}')
            if not _valid_candidate(value):
                continue

            score = _candidate_score(
                value,
                min(left["confidence"], right["confidence"]),
                front=True,
            )

            if score < 50:
                continue

            evidence = _evidence(left["row"], value)
            if evidence:
                candidates.append({
                    "value": value,
                    "score": round(score + 10, 3),
                    "confidence": min(left["confidence"], right["confidence"]),
                    "evidence": evidence,
                    "source": "joined_front_panel_candidate",
                })

    return candidates


def identify_product(raw_text: str, ocr_data=None) -> dict[str, Any]:
    explicit_products, explicit_brands = _explicit_candidates(ocr_data)

    if explicit_products:
        selected = max(explicit_products, key=lambda item: item["score"])
    else:
        candidates = _front_candidates(ocr_data) + _joined_candidates(ocr_data)

        # Ordered global OCR is a fallback only. It helps when OCR text is
        # readable but the detector's boxes are fragmented or incomplete.
        for index, line in enumerate(str(raw_text or "").splitlines()):
            value = _clean_candidate(line)
            if not _valid_candidate(value):
                continue
            score = _candidate_score(value, 0.5, front=index < 10)
            if score >= 35:
                candidates.append({
                    "value": value,
                    "score": round(score, 3),
                    "confidence": 0.5,
                    "evidence": None,
                    "source": "global_ocr_candidate",
                })

        selected = max(candidates, key=lambda item: item["score"]) if candidates else None

    brand = max(explicit_brands, key=lambda item: item["confidence"]) if explicit_brands else None

    output_candidates = sorted(
        [dict(item, row=None) for item in (explicit_products + (_front_candidates(ocr_data) if not explicit_products else []))],
        key=lambda item: item["score"],
        reverse=True,
    )

    return {
        "product_name": selected["value"] if selected else None,
        "product_name_confidence": selected["confidence"] if selected else None,
        "product_name_evidence": selected["evidence"] if selected else None,
        "brand": brand["value"] if brand else None,
        "brand_confidence": brand["confidence"] if brand else None,
        "brand_evidence": brand["evidence"] if brand else None,
        "product_name_candidates": output_candidates[:10],
        "brand_candidates": explicit_brands[:5],
    }
