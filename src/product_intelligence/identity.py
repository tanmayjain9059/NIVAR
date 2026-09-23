"""Evidence-based product and brand identity extraction for packaged foods."""

import re
from typing import Any

PRODUCT_LABEL_RE = re.compile(
    r"\b(?:product\s+name|name\s+of\s+(?:the\s+)?(?:product|food))\b"
    r"\s*[:\-]?\s*(.+)",
    re.I,
)

BRAND_LABEL_RE = re.compile(
    r"\bbrand\b\s*[:\-]?\s*(.+)",
    re.I,
)

MANUFACTURER_RE = re.compile(
    r"\b(?:manufactured|marketed|packed|imported)\s+by\b"
    r"\s*[:\-]?\s*(.+)",
    re.I,
)

NOISE_RE = re.compile(
    r"\b(?:mrp|m\.r\.p|net\s*(?:qty|quantity|weight)|ingredients?|"
    r"nutrition(?:al)?|energy|protein|carbohydrate|sugars?|fat|fiber|"
    r"sodium|cholesterol|saturated|trans\s*fat|batch|lot|pkd|mfd|mfg|"
    r"barcode|use\s*by|best\s*before|expiry|country\s+of\s+origin|"
    r"contains|may\s+contain|keep\s+in|store\s+in|directions|warning|"
    r"license|licence|fssai|customer\s+care|consumer\s+care|"
    r"manufactured|packed|marketed|imported|www\.|@)\b",
    re.I,
)

COMPANY_RE = re.compile(
    r"\b(?:pvt\.?\s*ltd\.?|private\s+limited|ltd\.?|limited|llp|"
    r"inc\.?|incorporated|corp\.?|corporation|company|industries|"
    r"food\s+products|enterprises|traders|manufacturers?)\b",
    re.I,
)

ADDRESS_RE = re.compile(
    r"\b(?:plot|road|street|lane|avenue|industrial\s+area|estate|"
    r"sector|block|district|taluka|tehsil|village|nagar|colony|"
    r"pin(?:code)?|postcode|zip|near|opposite|opp\.?|phase|highway|"
    r"city|state)\b",
    re.I,
)

FOOD_WORDS = re.compile(
    r"\b(?:rice|basmati|flour|atta|maida|suji|sooji|dal|lentil|pulses?|"
    r"wheat|oats?|poha|flattened\s+rice|noodles?|pasta|biscuit(?:s)?|"
    r"cookies?|bread|rusk|namkeen|snack(?:s)?|chips?|mixture|cereal(?:s)?|"
    r"corn(?:flakes)?|muesli|chocolate|cocoa|tea|coffee|juice|drink|"
    r"beverage|milk|curd|yogurt|ghee|butter|cheese|oil|pickle|jam|sauce|"
    r"ketchup|spice(?:s)?|masala|salt|sugar|honey|jaggery|vermicelli|"
    r"semolina|gram|chana|rajma|peas?|nuts?|almonds?|cashews?|seasoning|"
    r"powder|mix|blend|paste)\b",
    re.I,
)

MARKETING_RE = re.compile(
    r"\b(?:everyone|gathered|moments|warmth|finest|first\s+bite|"
    r"last\s+crumb|heaven|sharing|loved\s+ones|discover|range|baked|"
    r"buttery|meant\s+for|clinking|crunch|snacktime)\b",
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

    if not 2 <= len(text) <= 100:
        return False

    if re.fullmatch(r"[\d\s./:%₹$€£+\-]+", text):
        return False

    if NOISE_RE.search(text):
        return False

    if COMPANY_RE.search(text) or ADDRESS_RE.search(text):
        return False

    if sum(c.isalpha() for c in text) < 2:
        return False

    return len(text.split()) <= 10


def _clean_manufacturer_brand(value: str) -> str:
    """Turn a manufacturer-role value into a conservative brand candidate."""
    value = _clean(value)

    stop = re.search(
        r"\b(?:fssai|licen[cs]e|plot|road|street|lane|avenue|industrial\s+area|"
        r"estate|sector|block|district|taluka|tehsil|village|nagar|colony|"
        r"pin(?:code)?|postcode|zip|near|opposite|opp\.?|phase|highway|"
        r"city|state|phone|tel|toll[-\s]?free|customer\s+care|"
        r"consumer\s+care|www\.|@)\b",
        value,
        re.I,
    )
    if stop:
        value = value[:stop.start()]

    value = _clean(value)

    value = re.sub(
        r"\s+(?:pvt\.?\s*ltd\.?|private\s+limited|ltd\.?|limited|"
        r"llp|inc\.?|incorporated|corp\.?|corporation|company|"
        r"industries|food\s+products|foods|enterprises|traders|manufacturers?)\.?(?:\s+.*)?$",
        "",
        value,
        flags=re.I,
    )

    return _clean(value)


def _score(
    text: str,
    confidence: float,
    *,
    front: bool,
    source: str,
) -> float:
    value = _clean(text)
    score = confidence * 100

    if FOOD_WORDS.search(value):
        score += 55
    else:
        score += 5

    word_count = len(value.split())

    if 1 <= word_count <= 5:
        score += 12
    elif word_count > 8:
        score -= 20

    if 4 <= len(value) <= 60:
        score += 5

    if front:
        score += 35

    if source == "explicit_product_label":
        score += 80

    if MARKETING_RE.search(value):
        score -= 60

    if "!" in value or "?" in value:
        score -= 25

    return score


def _candidate(
    value: str,
    row=None,
    *,
    confidence: float | None = None,
    source: str,
    front: bool,
    evidence_text: str | None = None,
) -> dict[str, Any] | None:
    value = _clean(value)

    if not _valid_candidate(value):
        return None

    if confidence is None:
        confidence = (
            _confidence(row.get("conf", 0))
            if row is not None
            else 0.5
        )

    evidence = (
        _evidence(row, evidence_text if evidence_text is not None else value)
        if row is not None
        else None
    )

    return {
        "value": value,
        "confidence": confidence,
        "score": round(
            _score(
                value,
                confidence,
                front=front,
                source=source,
            ),
            3,
        ),
        "evidence": evidence,
        "source": source,
    }


def _rows(ocr_data):
    if ocr_data is None or getattr(ocr_data, "empty", True):
        return []

    rows = []

    for _, row in ocr_data.iterrows():
        text = _clean(row.get("text"))

        if text:
            rows.append(row)

    return rows


def _explicit_candidates(ocr_data):
    products = []
    brands = []

    for row in _rows(ocr_data):
        text = _clean(row.get("text"))
        confidence = _confidence(row.get("conf", 0))

        match = PRODUCT_LABEL_RE.search(text)
        if match:
            candidate = _candidate(
                match.group(1),
                row,
                confidence=confidence,
                source="explicit_product_label",
                front=True,
                evidence_text=text,
            )

            if candidate:
                products.append(candidate)

        match = BRAND_LABEL_RE.search(text)
        if match:
            candidate = _candidate(
                match.group(1),
                row,
                confidence=confidence,
                source="explicit_brand_label",
                front=True,
                evidence_text=text,
            )

            if candidate:
                brands.append(candidate)

        match = MANUFACTURER_RE.search(text)
        if match:
            candidate = _candidate(
                _clean_manufacturer_brand(match.group(1)),
                row,
                confidence=min(confidence, 0.9),
                source="manufacturer_entity",
                front=False,
                evidence_text=text,
            )

            if candidate:
                brands.append(candidate)

    return products, brands


def _row_box_dimensions(row):
    try:
        left = float(row["left"])
        top = float(row["top"])
        right = float(row["right"])
        bottom = float(row["bottom"])
    except (KeyError, TypeError, ValueError):
        return None
    return left, top, right, bottom


def _front_candidates(ocr_data):
    rows = _rows(ocr_data)

    if not rows:
        return []

    try:
        image_height = max(
            float(ocr_data["bottom"].max()),
            1.0,
        )
    except (KeyError, TypeError, ValueError):
        return []

    candidates = []

    for row in rows:
        text = _clean(row.get("text"))

        try:
            ratio = float(row["top"]) / image_height
        except (KeyError, TypeError, ValueError):
            continue

        if ratio > 0.48:
            continue

        candidate = _candidate(
            text,
            row,
            source="front_panel_ocr",
            front=ratio < 0.35,
        )

        if candidate:
            candidates.append(candidate)

    return candidates


def _joined_front_candidates(ocr_data):
    rows = _rows(ocr_data)

    if not rows:
        return []

    try:
        image_height = max(
            float(ocr_data["bottom"].max()),
            1.0,
        )
    except (KeyError, TypeError, ValueError):
        return []

    ordered = []

    for row in rows:
        try:
            top = float(row["top"])
            bottom = float(row["bottom"])
            left = float(row["left"])
            right = float(row["right"])
        except (KeyError, TypeError, ValueError):
            continue

        if top / image_height > 0.48:
            continue

        ordered.append(
            {
                "row": row,
                "top": top,
                "bottom": bottom,
                "left": left,
                "right": right,
                "height": max(1.0, bottom - top),
            }
        )

    ordered.sort(
        key=lambda item: (item["top"], item["left"]),
    )

    candidates = []

    for index, left in enumerate(ordered):
        for right in ordered[index + 1:]:
            if right["left"] < left["right"]:
                continue

            left_center = (left["top"] + left["bottom"]) / 2
            right_center = (right["top"] + right["bottom"]) / 2

            height_limit = max(
                0.7 * max(left["height"], right["height"]),
                24,
            )

            if abs(left_center - right_center) > height_limit:
                if right["top"] - left["top"] > height_limit:
                    break
                continue

            gap = right["left"] - left["right"]

            if gap > 5 * max(left["height"], 20):
                continue

            value = _clean(
                f'{left["row"].get("text", "")} '
                f'{right["row"].get("text", "")}',
            )

            candidate = _candidate(
                value,
                left["row"],
                confidence=min(
                    _confidence(left["row"].get("conf", 0)),
                    _confidence(right["row"].get("conf", 0)),
                ),
                source="joined_front_panel_ocr",
                front=True,
            )

            if candidate:
                candidates.append(candidate)

    return candidates


def identify_product(
    raw_text: str,
    ocr_data=None,
) -> dict[str, Any]:
    explicit_products, explicit_brands = _explicit_candidates(ocr_data)

    if explicit_products:
        product_candidates = explicit_products
    else:
        product_candidates = (
            _front_candidates(ocr_data)
            + _joined_front_candidates(ocr_data)
        )

        # Global OCR is a final recall source. It is intentionally penalized
        # so that it cannot outrank spatial front-panel evidence.
        for line in str(raw_text or "").splitlines():
            candidate = _candidate(
                line,
                source="global_ocr_fallback",
                front=False,
                confidence=0.5,
            )

            if candidate:
                candidate["score"] -= 20
                product_candidates.append(candidate)

    selected = (
        max(
            product_candidates,
            key=lambda item: item["score"],
        )
        if product_candidates
        else None
    )

    # A caller may provide a clean single OCR row without a front-panel
    # heuristic being applicable. Preserve that as explicit evidence.
    if selected is None and ocr_data is not None:
        rows = _rows(ocr_data)
        if len(rows) == 1:
            row = rows[0]
            text = _clean(row.get("text"))
            candidate = _candidate(
                text,
                row,
                source="single_row_ocr_fallback",
                front=False,
            )
            if candidate:
                selected = candidate
                product_candidates.append(candidate)

    brand = (
        max(
            explicit_brands,
            key=lambda item: item["confidence"],
        )
        if explicit_brands
        else None
    )

    candidates = sorted(
        [dict(item) for item in product_candidates],
        key=lambda item: item["score"],
        reverse=True,
    )[:12]

    return {
        "product_name": (
            selected["value"]
            if selected
            else None
        ),
        "product_name_confidence": (
            selected["confidence"]
            if selected
            else None
        ),
        "product_name_evidence": (
            selected["evidence"]
            if selected
            else None
        ),
        "brand": (
            brand["value"]
            if brand
            else None
        ),
        "brand_confidence": (
            brand["confidence"]
            if brand
            else None
        ),
        "brand_evidence": (
            brand["evidence"]
            if brand
            else None
        ),
        "product_name_candidates": candidates,
        "brand_candidates": explicit_brands[:5],
    }
