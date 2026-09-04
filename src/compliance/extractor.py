"""
Legal Metrology declaration extraction from OCR text.

This module performs first-pass extraction of mandatory packaged-
commodity declarations and attaches OCR evidence when available.

Extraction philosophy:
    label detection
        -> candidate value generation
        -> spatial / textual association
        -> positive + negative evidence
        -> conservative result

This is an extraction layer, not a legal compliance certification.
"""

import re


# ============================================================================
# GENERIC HELPERS
# ============================================================================

def _search(pattern, text, flags=re.IGNORECASE):
    """Return the first regex match or None."""
    return re.search(pattern, text or "", flags)


def _normalize_text(text):
    """Normalize OCR text for loose comparison."""
    return re.sub(
        r"\s+",
        " ",
        str(text or "").strip(),
    ).lower()


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bbox_from_row(row):
    """Build a normalized evidence bounding box."""
    try:
        return {
            "x1": int(float(row["left"])),
            "y1": int(float(row["top"])),
            "x2": int(float(row["right"])),
            "y2": int(float(row["bottom"])),
        }
    except (KeyError, TypeError, ValueError):
        return None


def _evidence_from_row(row, text_override=None):
    """Create OCR evidence from a dataframe row."""
    bbox = _bbox_from_row(row)

    if bbox is None:
        return None

    return {
        "text": (
            str(text_override).strip()
            if text_override is not None
            else str(row.get("text", "")).strip()
        ),
        "confidence": _safe_float(row.get("conf", 0)),
        "bbox": bbox,
    }


def _find_evidence(matched_text, ocr_data):
    """
    Find the OCR row that best corresponds to matched text.
    """
    if not matched_text or ocr_data is None:
        return None

    if getattr(ocr_data, "empty", True):
        return None

    target = _normalize_text(matched_text)

    if not target:
        return None

    best_match = None
    best_score = 0.0

    for _, row in ocr_data.iterrows():
        row_text = str(row.get("text", "")).strip()

        if not row_text:
            continue

        normalized = _normalize_text(row_text)

        if not normalized:
            continue

        if normalized == target:
            score = 1.0
        elif target in normalized:
            score = 0.92
        elif normalized in target:
            score = 0.82
        else:
            continue

        if score <= best_score:
            continue

        evidence = _evidence_from_row(row)

        if evidence is None:
            continue

        best_match = evidence
        best_score = score

    return best_match


def _result(pattern, ocr_data=None):
    """Convert regex match to standard extractor result."""
    matched_text = pattern.group(0) if pattern else None

    result = {
        "detected": bool(pattern),
        "matched_text": matched_text,
    }

    evidence = _find_evidence(
        matched_text,
        ocr_data,
    )

    if evidence:
        result["evidence"] = evidence

    return result


# ============================================================================
# SHARED OCR / SPATIAL HELPERS
# ============================================================================

def _find_label_rows(label_regex, ocr_data):
    """Find OCR rows containing a declaration label."""
    if ocr_data is None or getattr(ocr_data, "empty", True):
        return []

    rows = []

    for _, row in ocr_data.iterrows():
        text = str(row.get("text", "")).strip()

        if not text:
            continue

        if re.search(
            label_regex,
            text,
            re.IGNORECASE,
        ):
            rows.append(row)

    return rows


def _spatial_candidates(
    label_row,
    ocr_data,
    value_matcher,
    *,
    max_right_gap=450,
    max_right_y_diff=180,
    max_below_gap=500,
    max_below_x_diff=500,
):
    """
    Find value OCR rows spatially associated with a label.

    Supported layouts:

        LABEL VALUE

    and:

        LABEL
        VALUE
    """
    if ocr_data is None or getattr(ocr_data, "empty", True):
        return []

    try:
        label_left = float(label_row["left"])
        label_top = float(label_row["top"])
        label_right = float(label_row["right"])
        label_bottom = float(label_row["bottom"])
    except (KeyError, TypeError, ValueError):
        return []

    label_cx = (label_left + label_right) / 2
    label_cy = (label_top + label_bottom) / 2

    candidates = []

    for _, row in ocr_data.iterrows():
        if row.name == label_row.name:
            continue

        candidate_text = str(row.get("text", "")).strip()

        if not candidate_text:
            continue

        match = value_matcher(candidate_text)

        if not match:
            continue

        try:
            left = float(row["left"])
            top = float(row["top"])
            right = float(row["right"])
            bottom = float(row["bottom"])
        except (KeyError, TypeError, ValueError):
            continue

        center_x = (left + right) / 2
        center_y = (top + bottom) / 2

        right_gap = left - label_right
        right_y_diff = abs(center_y - label_cy)

        below_gap = top - label_bottom
        below_x_diff = abs(center_x - label_cx)

        is_right = (
            right_gap >= 0
            and right_gap <= max_right_gap
            and right_y_diff <= max_right_y_diff
        )

        is_below = (
            below_gap >= 0
            and below_gap <= max_below_gap
            and below_x_diff <= max_below_x_diff
        )

        if not (is_right or is_below):
            continue

        confidence = _safe_float(
            row.get("conf", 0)
        )

        if is_right:
            geometry_score = (
                100
                - right_gap * 0.12
                - right_y_diff * 0.20
            )
            layout = "right"
        else:
            geometry_score = (
                90
                - below_gap * 0.10
                - below_x_diff * 0.08
            )
            layout = "below"

        candidates.append(
            {
                "row": row,
                "text": candidate_text,
                "match": match,
                "confidence": confidence,
                "geometry_score": geometry_score,
                "layout": layout,
            }
        )

    return candidates


def _best_spatial_candidate(candidates):
    """Return the strongest spatial candidate."""
    if not candidates:
        return None

    candidates.sort(
        key=lambda candidate: (
            candidate["geometry_score"]
            + candidate["confidence"] * 25
        ),
        reverse=True,
    )

    return candidates[0]


# ============================================================================
# MANUFACTURER / PACKER / IMPORTER
# ============================================================================

MANUFACTURER_LABEL_REGEX = (
    r"(?:"
    r"manufactured\s+by"
    r"|packed\s+by"
    r"|marketed\s+by"
    r"|imported\s+by"
    r"|mfg\.?\s*(?:&|and)\s*mkt\.?\s*by"
    r")"
)


def extract_manufacturer(text, ocr_data=None):
    """
    Detect manufacturer / packer / marketer / importer wording.

    'Manufactured by' is explicitly a manufacturer declaration,
    not a manufacture-date declaration.
    """
    pattern = _search(
        MANUFACTURER_LABEL_REGEX,
        text,
    )

    return _result(
        pattern,
        ocr_data,
    )


# ============================================================================
# NET QUANTITY
# ============================================================================

NET_QUANTITY_LABEL_REGEX = (
    r"(?:"
    r"net\s+(?:weight|quantity|qty)"
    r"|n\.?\s*qty"
    r")"
)

NET_QUANTITY_VALUE_REGEX = re.compile(
    r"^\s*"
    r"(\d+(?:\.\d+)?)"
    r"\s*"
    r"(g|gm|gms|kg|mg|ml|l|ltr|litre|liter|pcs|pieces|pc|n)"
    r"\s*$",
    re.IGNORECASE,
)


def _match_net_quantity_value(value):
    return NET_QUANTITY_VALUE_REGEX.fullmatch(value)


def _clean_net_quantity(match):
    return f"{match.group(1)} {match.group(2)}"


def extract_net_quantity(text, ocr_data=None):
    """
    Detect net quantity only when explicitly associated with
    net-quantity wording.
    """
    text = text or ""

    # ------------------------------------------------------------------
    # Same-line
    # ------------------------------------------------------------------
    contextual_pattern = _search(
        NET_QUANTITY_LABEL_REGEX
        + r"\s*[:=\-]?\s*"
        + r"(\d+(?:\.\d+)?)"
        + r"\s*"
        + r"(g|gm|gms|kg|mg|ml|l|ltr|litre|liter|pcs|pieces|pc|n)"
        + r"\b",
        text,
    )

    if contextual_pattern:
        result = {
            "detected": True,
            "matched_text": contextual_pattern.group(0),
        }

        evidence = _find_evidence(
            contextual_pattern.group(0),
            ocr_data,
        )

        if evidence:
            result["evidence"] = evidence

        return result

    # ------------------------------------------------------------------
    # Spatial
    # ------------------------------------------------------------------
    label_rows = _find_label_rows(
        NET_QUANTITY_LABEL_REGEX,
        ocr_data,
    )

    candidates = []

    for label_row in label_rows:
        spatial = _spatial_candidates(
            label_row,
            ocr_data,
            _match_net_quantity_value,
            max_right_gap=500,
            max_right_y_diff=180,
            max_below_gap=450,
            max_below_x_diff=350,
        )

        for candidate in spatial:
            candidate["label_row"] = label_row

            candidates.append(candidate)

    best = _best_spatial_candidate(candidates)

    if best:
        value = _clean_net_quantity(
            best["match"]
        )

        evidence = _evidence_from_row(
            best["row"],
            text_override=value,
        )

        result = {
            "detected": True,
            "matched_text": (
                f"{str(best['label_row'].get('text', '')).strip()} "
                f"{value}"
            ),
        }

        if evidence:
            result["evidence"] = evidence

        return result

    # ------------------------------------------------------------------
    # Label exists but value missing
    # ------------------------------------------------------------------
    label_pattern = _search(
        NET_QUANTITY_LABEL_REGEX,
        text,
    )

    if label_pattern:
        result = {
            "detected": True,
            "matched_text": label_pattern.group(0),
            "value_missing": True,
        }

        evidence = _find_evidence(
            label_pattern.group(0),
            ocr_data,
        )

        if evidence:
            result["evidence"] = evidence

        return result

    return {
        "detected": False,
        "matched_text": None,
    }


# ============================================================================
# MANUFACTURE / PACKING DATE
# ============================================================================
MANUFACTURE_DATE_LABEL_REGEX = (
    r"(?:"
    r"\bmfd\b"
    r"|"
    r"\bmfg(?:\.?\s*date)?\b"
    r"|"
    r"\bmanufacture(?:d)?\s+date\b"
    r"|"
    r"\bmanufactured(?!\s+by\b)"
    r"|"
    r"\bpkd\b"
    r"|"
    r"\bpacked\b"
    r"|"
    r"\bdate\s+of\s+packaging\b"
    r")"
)

MONTH_NAME_REGEX = (
    r"(?:"
    r"jan(?:uary)?"
    r"|feb(?:ruary)?"
    r"|mar(?:ch)?"
    r"|apr(?:il)?"
    r"|may"
    r"|jun(?:e)?"
    r"|jul(?:y)?"
    r"|aug(?:ust)?"
    r"|sep(?:t(?:ember)?)?"
    r"|oct(?:ober)?"
    r"|nov(?:ember)?"
    r"|dec(?:ember)?"
    r")"
)
DATE_VALUE_CORE_REGEX = (
    r"(?:"
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|"
    + r"\d{1,2}[/-]" + MONTH_NAME_REGEX + r"[/-]\d{2,4}"
    + r"|"
    + MONTH_NAME_REGEX + r"[/-]\d{2,4}"
    + r"|"
    + r"\d{1,2}" + MONTH_NAME_REGEX + r"\d{2,4}"
    + r")"
)

DATE_VALUE_REGEX = re.compile(
    r"^\s*" + DATE_VALUE_CORE_REGEX + r"\s*$",
    re.IGNORECASE,
)

DATE_VALUE_CORE_REGEX = (
    r"(?:"
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|"
    r"\d{1,2}[/-]" + MONTH_NAME_REGEX + r"[/-]\d{2,4}"
    r"|"
    + MONTH_NAME_REGEX
    + r"[/-]\d{2,4}"
    + r"|"
    + r"\d{1,2}"
    + MONTH_NAME_REGEX
    + r"\d{2,4}"
    + r")"
)

DATE_VALUE_REGEX = re.compile(
    r"^\s*" + DATE_VALUE_CORE_REGEX + r"\s*$",
    re.IGNORECASE,
)
DATE_NEGATIVE_REGEX = re.compile(
    r"(?:"
    r"\bbest\s+before\b"
    r"|"
    r"\bbest\s+before\s+end\b"
    r"|"
    r"\buse\s+by\b"
    r"|"
    r"\bexpiry\b"
    r"|"
    r"\bexpires\b"
    r"|"
    r"\bexp\b"
    r"|"
    r"\bexp\.?\s*date\b"
    r"|"
    r"\bexpiry\s+date\b"
    r")",
    re.IGNORECASE,
)


def _match_date_value(value):
    return DATE_VALUE_REGEX.fullmatch(value)


def _date_label_is_negative(label_text):
    return bool(
        DATE_NEGATIVE_REGEX.search(
            str(label_text or "")
        )
    )


def extract_manufacture_date(text, ocr_data=None):
    """
    Detect manufacture / packing dates.

    Important semantic distinction:

        Manufactured by -> manufacturer
        Manufactured 14/11/2024 -> manufacture date

    Expiry / best-before / use-by dates are excluded.
    """
    text = text or ""

    # ------------------------------------------------------------------
    # Same-line / attached date
    # ------------------------------------------------------------------
    contextual_pattern = _search(
        MANUFACTURE_DATE_LABEL_REGEX
        + r"\s*[\.:=\-]?\s*"
        + r"("
        + DATE_VALUE_CORE_REGEX
        + r")",
        text,
    )

    if contextual_pattern:
        matched_text = contextual_pattern.group(0)

        if not DATE_NEGATIVE_REGEX.search(
            matched_text
        ):
            result = {
                "detected": True,
                "matched_text": matched_text,
            }

            evidence = _find_evidence(
                matched_text,
                ocr_data,
            )

            if evidence:
                result["evidence"] = evidence

            return result

    # ------------------------------------------------------------------
    # Spatial
    # ------------------------------------------------------------------
    label_rows = _find_label_rows(
        MANUFACTURE_DATE_LABEL_REGEX,
        ocr_data,
    )

    candidates = []

    for label_row in label_rows:
        label_text = str(
            label_row.get("text", "")
        ).strip()

        if _date_label_is_negative(
            label_text
        ):
            continue

        spatial = _spatial_candidates(
            label_row,
            ocr_data,
            _match_date_value,
            max_right_gap=450,
            max_right_y_diff=180,
            max_below_gap=500,
            max_below_x_diff=450,
        )

        for candidate in spatial:
            candidate_text = candidate["text"]

            if DATE_NEGATIVE_REGEX.search(
                candidate_text
            ):
                continue

            label_lower = label_text.lower()

            if re.search(
                r"\b(?:mfd|mfg|pkd)\b",
                label_lower,
            ):
                candidate["geometry_score"] += 20

            if "date" in label_lower:
                candidate["geometry_score"] += 10

            candidate["label_row"] = label_row
            candidates.append(candidate)

    best = _best_spatial_candidate(
        candidates
    )

    if best:
        evidence = _evidence_from_row(
            best["row"]
        )

        result = {
            "detected": True,
            "matched_text": (
                f"{str(best['label_row'].get('text', '')).strip()}\n"
                f"{best['text']}"
            ),
        }

        if evidence:
            result["evidence"] = evidence

        return result

    # ------------------------------------------------------------------
    # Label exists but value missing
    # ------------------------------------------------------------------
    label_pattern = _search(
        MANUFACTURE_DATE_LABEL_REGEX,
        text,
    )

    if label_pattern:
        result = {
            "detected": True,
            "matched_text": label_pattern.group(0),
            "value_missing": True,
        }

        evidence = _find_evidence(
            label_pattern.group(0),
            ocr_data,
        )

        if evidence:
            result["evidence"] = evidence

        return result

    return {
        "detected": False,
        "matched_text": None,
    }


# ============================================================================
# MRP
# ============================================================================

MRP_LABEL_REGEX = (
    r"(?:"
    r"\bm\s*\.?\s*r\s*\.?\s*p\s*\.?"
    r"|"
    r"\bmaximum\s+retail\s+price\b"
    r"|"
    r"\bretail\s+sale\s+price\b"
    r")"
)


MRP_NUMBER_REGEX = re.compile(
    r"^\s*(?:"
    r"₹\s*"
    r"|rs\.?\s*"
    r"|inr\s*"
    r")?"
    r"(\d{1,5}(?:\.\d{1,2})?)"
    r"\s*$",
    re.IGNORECASE,
)


DATE_LIKE_TOKEN_REGEX = re.compile(
    r"^\s*"
    r"\d{1,4}[./-]\d{1,4}[./-]\d{1,4}"
    r"\s*$"
)


UNIT_PRICE_REGEX = re.compile(
    r"(?:"
    r"₹|rs\.?|inr"
    r")?\s*\d+(?:\.\d{1,2})?\s*/\s*"
    r"(?:g|kg|mg|ml|l|unit|piece|pc)\b",
    re.IGNORECASE,
)


UNIT_VALUE_REGEX = re.compile(
    r"\b(?:"
    r"g|gm|gms|kg|mg|ml|l|ltr|litre|liter|pcs|pieces|pc"
    r")\b",
    re.IGNORECASE,
)


def _clean_mrp_candidate(value):
    """
    Validate a possible MRP value.

    Rejects:
        dates
        unit prices
        quantities
        non-numeric fragments
    """
    value = str(value or "").strip()

    if not value:
        return None

    if DATE_LIKE_TOKEN_REGEX.fullmatch(value):
        return None

    if UNIT_PRICE_REGEX.search(value):
        return None

    if UNIT_VALUE_REGEX.search(value):
        return None

    match = MRP_NUMBER_REGEX.fullmatch(value)

    if not match:
        return None

    numeric_value = match.group(1)

    try:
        number = float(numeric_value)
    except ValueError:
        return None

    if number <= 0:
        return None

    return numeric_value


def _match_mrp_value(value):
    """
    Match a complete OCR token as an MRP value.
    """
    value = str(value or "").strip()

    if not value:
        return None

    cleaned = _clean_mrp_candidate(value)

    if cleaned is None:
        return None

    return re.fullmatch(
        r"\d{1,5}(?:\.\d{1,2})?",
        cleaned,
    )


def extract_mrp(text, ocr_data=None):
    """
    Detect Maximum Retail Price conservatively.

    Supports:

        MRP 180
        MRP180
        MRP: ₹180
        M.R.P. 180
        M. R. P. 180
        M.R.P.. 235.35
    """
    text = text or ""

    # ------------------------------------------------------------------
    # Same-line / attached
    # ------------------------------------------------------------------
    for line in text.splitlines():
        if not re.search(
            MRP_LABEL_REGEX,
            line,
            re.IGNORECASE,
        ):
            continue

        match = re.search(
            MRP_LABEL_REGEX
            + r"\s*[:=\-\.]?\s*"
            + r"(?:₹\s*|rs\.?\s*|inr\s*)?"
            + r"(\d{1,5}(?:\.\d{1,2})?)",
            line,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = _clean_mrp_candidate(
            match.group(1)
        )

        if value is None:
            continue

        result = {
            "detected": True,
            "matched_text": match.group(0),
        }

        evidence = _find_evidence(
            match.group(0),
            ocr_data,
        )

        if evidence:
            result["evidence"] = evidence

        return result

    # ------------------------------------------------------------------
    # Spatial
    # ------------------------------------------------------------------
    label_rows = _find_label_rows(
        MRP_LABEL_REGEX,
        ocr_data,
    )

    candidates = []

    for label_row in label_rows:
        label_text = str(
            label_row.get("text", "")
        ).strip()

        # Attached value inside same OCR token.
        attached_match = re.search(
            MRP_LABEL_REGEX
            + r"\s*[:=\-\.]?\s*"
            + r"(?:₹\s*|rs\.?\s*|inr\s*)?"
            + r"(\d{1,5}(?:\.\d{1,2})?)",
            label_text,
            re.IGNORECASE,
        )

        if attached_match:
            value = _clean_mrp_candidate(
                attached_match.group(1)
            )

            if value:
                result = {
                    "detected": True,
                    "matched_text": f"MRP {value}",
                }

                evidence = _evidence_from_row(
                    label_row
                )

                if evidence:
                    result["evidence"] = evidence

                return result

        spatial = _spatial_candidates(
            label_row,
            ocr_data,
            _match_mrp_value,
            max_right_gap=700,
            max_right_y_diff=220,
            max_below_gap=600,
            max_below_x_diff=500,
        )

        for candidate in spatial:
            candidate["label_row"] = label_row

            candidate_text = candidate["text"]

            if DATE_LIKE_TOKEN_REGEX.fullmatch(
                candidate_text
            ):
                candidate["geometry_score"] -= 200

            if UNIT_PRICE_REGEX.search(
                candidate_text
            ):
                candidate["geometry_score"] -= 200

            if UNIT_VALUE_REGEX.search(
                candidate_text
            ):
                candidate["geometry_score"] -= 200

            candidates.append(candidate)

    valid_candidates = [
        candidate
        for candidate in candidates
        if candidate["geometry_score"] > 0
    ]

    best = _best_spatial_candidate(
        valid_candidates
    )

    if best:
        value = _clean_mrp_candidate(
            best["text"]
        )

        if value:
            result = {
                "detected": True,
                "matched_text": (
                    f"{str(best['label_row'].get('text', '')).strip()} "
                    f"{value}"
                ),
            }

            evidence = _evidence_from_row(
                best["row"],
                text_override=best["text"],
            )

            if evidence:
                result["evidence"] = evidence

            return result

    # ------------------------------------------------------------------
    # Label exists but value missing
    # ------------------------------------------------------------------
    label_pattern = _search(
        MRP_LABEL_REGEX,
        text,
    )

    if label_pattern:
        result = {
            "detected": True,
            "matched_text": label_pattern.group(0),
            "value_missing": True,
        }

        evidence = _find_evidence(
            label_pattern.group(0),
            ocr_data,
        )

        if evidence:
            result["evidence"] = evidence

        return result

    return {
        "detected": False,
        "matched_text": None,
    }


# ============================================================================
# CONSUMER CARE
# ============================================================================

def extract_consumer_care(text, ocr_data=None):
    """
    Detect consumer-care / complaint contact information.
    """
    text = text or ""

    care_pattern = _search(
        r"(consumer\s+care|"
        r"customer\s+care|"
        r"consumer\s+complaints?|"
        r"customer\s+complaints?|"
        r"customer\s+service|"
        r"consumer\s+service)",
        text,
    )

    complaint_pattern = _search(
        r"(?:in\s+case\s+of\s+any\s+)?"
        r"(?:complaint|complaints)",
        text,
    )

    contact_pattern = _search(
        r"(write\s+to|"
        r"contact\s+us|"
        r"reach\s+us|"
        r"email\s+us|"
        r"call\s+us|"
        r"write\s+us)",
        text,
    )

    tollfree_pattern = _search(
        r"(?:toll[\s-]*free|"
        r"helpline|"
        r"help\s*line|"
        r"hotline)",
        text,
    )

    email_pattern = _search(
        r"\b[a-z0-9._%+\-]+"
        r"@[a-z0-9.\-]+\.[a-z]{2,}\b",
        text,
    )

    phone_pattern = _search(
        r"\b(?:1800|1860)"
        r"[\s-]?"
        r"\d{2,4}"
        r"[\s-]?"
        r"\d{3,4}\b",
        text,
    )

    matched = next(
        (
            pattern
            for pattern in (
                care_pattern,
                complaint_pattern,
                contact_pattern,
                tollfree_pattern,
                email_pattern,
                phone_pattern,
            )
            if pattern
        ),
        None,
    )

    result = {
        "detected": matched is not None,
        "matched_text": (
            matched.group(0)
            if matched
            else None
        ),
    }

    if matched:
        evidence = _find_evidence(
            matched.group(0),
            ocr_data,
        )

        if evidence:
            result["evidence"] = evidence

    return result


# ============================================================================
# COUNTRY OF ORIGIN
# ============================================================================

def extract_country_of_origin(text, ocr_data=None):
    pattern = _search(
        r"(country\s+of\s+origin|made\s+in)"
        r"\D{0,20}[a-z]+",
        text,
    )

    result = _result(
        pattern,
        ocr_data,
    )

    result["conditional"] = True

    return result


# ============================================================================
# MAIN EXTRACTION
# ============================================================================

def extract_declarations(
    raw_text,
    compliance_text=None,
    ocr_data=None,
):
    """
    Extract all currently supported declarations.

    Output contract is intentionally preserved for validator.py.
    """
    if compliance_text:
        text = (
            f"{compliance_text}\n"
            f"{raw_text or ''}"
        )
    else:
        text = raw_text or ""

    return {
        "manufacturer_packer_importer": (
            extract_manufacturer(
                text,
                ocr_data,
            )
        ),
        "net_quantity": (
            extract_net_quantity(
                text,
                ocr_data,
            )
        ),
        "manufacture_date": (
            extract_manufacture_date(
                text,
                ocr_data,
            )
        ),
        "mrp": (
            extract_mrp(
                text,
                ocr_data,
            )
        ),
        "consumer_care": (
            extract_consumer_care(
                text,
                ocr_data,
            )
        ),
        "country_of_origin": (
            extract_country_of_origin(
                text,
                ocr_data,
            )
        ),
    }