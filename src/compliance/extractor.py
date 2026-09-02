"""
Extraction of Legal Metrology declarations from OCR text.

The extractor detects declaration patterns and, when OCR dataframe
information is available, attaches the corresponding OCR evidence.
"""

import re


def _search(pattern, text, flags=re.IGNORECASE):
    """
    Return the first regex match or None.
    """
    return re.search(pattern, text, flags)


def _normalize_text(text):
    """
    Normalize text for loose matching between regex output
    and individual OCR rows.
    """
    return re.sub(r"\s+", " ", str(text or "").strip()).lower()


def _find_evidence(matched_text, ocr_data):
    """
    Find the OCR row that best corresponds to a regex match.

    Returns OCR text, confidence and bounding box when available.
    """
    if not matched_text or ocr_data is None:
        return None

    if getattr(ocr_data, "empty", True):
        return None

    target = _normalize_text(matched_text)

    if not target:
        return None

    best_match = None
    best_score = 0

    for _, row in ocr_data.iterrows():
        text = str(row.get("text", "")).strip()

        if not text:
            continue

        normalized = _normalize_text(text)

        if not normalized:
            continue

        # Exact OCR-row match.
        if normalized == target:
            score = 1.0

        # Regex may match only part of an OCR row.
        elif target in normalized:
            score = 0.9

        # OCR may contain a slightly different spacing.
        elif normalized in target:
            score = 0.8

        else:
            continue

        if score <= best_score:
            continue

        try:
            left = int(row["left"])
            top = int(row["top"])
            right = int(row["right"])
            bottom = int(row["bottom"])
            confidence = float(row["conf"])
        except (KeyError, TypeError, ValueError):
            continue

        best_match = {
            "text": text,
            "confidence": confidence,
            "bbox": {
                "x1": left,
                "y1": top,
                "x2": right,
                "y2": bottom,
            },
        }

        best_score = score

    return best_match


def _result(pattern, ocr_data=None):
    """
    Convert a regex match into the standard extractor result.
    """
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


def extract_manufacturer(text, ocr_data=None):
    pattern = _search(
        r"(manufactured|packed|marketed|imported)\s+by",
        text,
    )

    return _result(
        pattern,
        ocr_data,
    )


def extract_net_quantity(text, ocr_data=None):
    """
    Detect the declared net quantity.

    A quantity is considered reliable only when it is associated
    with explicit net-quantity wording. Serving size values are
    deliberately not accepted as net quantity.
    """

    text = text or ""

    # Explicit net-quantity context.
    contextual_pattern = _search(
        r"(?:net\s*(?:weight|quantity|qty))"
        r"\s*[:\-]?\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(g|gm|gms|kg|ml|l|litre|liter|ltr|pcs|pieces|n\b)",
        text,
    )

    if contextual_pattern:
        matched_text = (
            contextual_pattern.group(1)
            + " "
            + contextual_pattern.group(2)
        )

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

    # Net Weight / Net Quantity label exists,
    # but its numeric value was not detected.
    label_pattern = _search(
        r"(net\s*(?:weight|quantity|qty))",
        text,
    )

    if label_pattern:
        return {
            "detected": True,
            "matched_text": label_pattern.group(0),
            "value_missing": True,
        }

    # Do NOT fall back to arbitrary quantities.
    return {
        "detected": False,
        "matched_text": None,
    }

def extract_manufacture_date(text, ocr_data=None):
    pattern = _search(
        r"(mfg|mfd|pkd|packed on|manufactured on)"
        r"\D{0,10}"
        r"("
        r"\d{1,2}[/\-][a-z]{3,9}[/\-]\d{2,4}"
        r"|"
        r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}"
        r"|"
        r"[a-z]{3,9}\s*\d{4}"
        r")",
        text,
    )

    return _result(
        pattern,
        ocr_data,
    )

def extract_mrp(text, ocr_data=None):
    """
    Detect MRP only when the MRP label and numeric value are
    both available.

    If the MRP label is visible but the amount is missing,
    return a review-required result.
    """

    text = text or ""

    value_pattern = _search(
        r"(mrp|m\.r\.p|retail sale price)"
        r"\D{0,20}"
        r"(?:rs\.?|₹)?\s*"
        r"\d+(?:\.\d+)?",
        text,
    )

    if value_pattern:
        result = {
            "detected": True,
            "matched_text": value_pattern.group(0),
        }

        evidence = _find_evidence(
            result["matched_text"],
            ocr_data,
        )

        if evidence:
            result["evidence"] = evidence

        return result

    # Label exists, but value is not visible/detected.
    label_pattern = _search(
        r"(mrp|m\.r\.p|retail sale price)",
        text,
    )

    if label_pattern:
        return {
            "detected": True,
            "matched_text": label_pattern.group(0),
            "value_missing": True,
        }

    return {
        "detected": False,
        "matched_text": None,
    }

def extract_consumer_care(text, ocr_data=None):
    """
    Detect consumer-care / complaint contact information.

    Consumer-care information can appear in several forms:
      - Consumer Care / Customer Care
      - complaint-related wording
      - email address
      - customer-care phone number
      - "write to", "email", or "call" instructions

    The extractor is intentionally tolerant because OCR may split
    the declaration across multiple lines.
    """

    text = text or ""

    # --------------------------------------------------------
    # 1. Explicit consumer/customer care wording
    # --------------------------------------------------------

    care_pattern = _search(
        r"(consumer\s+care|customer\s+care)",
        text,
    )

    # --------------------------------------------------------
    # 2. Complaint/contact wording
    # --------------------------------------------------------

    complaint_pattern = _search(
        r"(?:in\s+case\s+of\s+any\s+)?complaint",
        text,
    )

    contact_pattern = _search(
        r"(write\s+to|contact\s+us|reach\s+us|email\s+us|call\s+us)",
        text,
    )

    # --------------------------------------------------------
    # 3. Email address
    # --------------------------------------------------------

    email_pattern = _search(
        r"\b[a-z0-9._%+-]+"
        r"@[a-z0-9.-]+"
        r"\.[a-z]{2,}\b",
        text,
    )

    # --------------------------------------------------------
    # 4. Indian consumer-care / toll-free phone number
    # --------------------------------------------------------

    phone_pattern = _search(
        r"\b(?:1800|1860)"
        r"[\s\-]?"
        r"\d{2,4}"
        r"[\s\-]?"
        r"\d{3,4}\b",
        text,
    )

    # --------------------------------------------------------
    # 5. Select strongest declaration
    # --------------------------------------------------------

    matched = None

    if care_pattern:
        matched = care_pattern

    elif complaint_pattern:
        matched = complaint_pattern

    elif contact_pattern:
        matched = contact_pattern

    elif email_pattern:
        matched = email_pattern

    elif phone_pattern:
        matched = phone_pattern

    # --------------------------------------------------------
    # 6. Build result
    # --------------------------------------------------------

    result = {
        "detected": bool(
            care_pattern
            or complaint_pattern
            or contact_pattern
            or email_pattern
            or phone_pattern
        ),
        "matched_text": (
            matched.group(0)
            if matched
            else None
        ),
    }

    # --------------------------------------------------------
    # 7. Attach OCR evidence
    # --------------------------------------------------------

    evidence = _find_evidence(
        result["matched_text"],
        ocr_data,
    )

    if evidence:
        result["evidence"] = evidence

    return result
    
    email_pattern = _search(
        r"[a-z0-9._%+-]+"
        r"@[a-z0-9.-]+\.[a-z]{2,}",
        text,
    )

    phone_pattern = _search(
        r"(consumer|customer)\s*care"
        r".{0,60}?"
        r"(\d[\d\s\-]{7,}\d)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    matched = None

    if email_pattern:
        matched = email_pattern
    elif phone_pattern:
        matched = phone_pattern

    result = {
        "detected": bool(
            email_pattern or phone_pattern
        ),
        "matched_text": (
            matched.group(0)
            if matched
            else None
        ),
    }

    evidence = _find_evidence(
        result["matched_text"],
        ocr_data,
    )

    if evidence:
        result["evidence"] = evidence

    return result


def extract_country_of_origin(text, ocr_data=None):
    pattern = _search(
        r"(country of origin|made in)"
        r"\D{0,20}[a-z]+",
        text,
    )

    result = _result(
        pattern,
        ocr_data,
    )

    result["conditional"] = True

    return result


def extract_declarations(
    raw_text,
    compliance_text=None,
    ocr_data=None,
):
    """
    Extract all currently supported declarations.

    The focused compliance OCR is searched first by placing it
    before the full-page OCR text.

    When ``ocr_data`` is supplied, matching OCR evidence is
    attached to detected declarations.
    """

    if compliance_text:
        text = (
            f"{compliance_text}\n"
            f"{raw_text or ''}"
        )
    else:
        text = raw_text or ""

    return {
        "manufacturer_packer_importer": extract_manufacturer(
            text,
            ocr_data,
        ),
        "net_quantity": extract_net_quantity(
            text,
            ocr_data,
        ),
        "manufacture_date": extract_manufacture_date(
            text,
            ocr_data,
        ),
        "mrp": extract_mrp(
            text,
            ocr_data,
        ),
        "consumer_care": extract_consumer_care(
            text,
            ocr_data,
        ),
        "country_of_origin": extract_country_of_origin(
            text,
            ocr_data,
        ),
    }