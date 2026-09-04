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
    return re.sub(
        r"\s+",
        " ",
        str(text or "").strip(),
    ).lower()


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
        text = str(
            row.get("text", "")
        ).strip()

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

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
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


def _find_nearby_value(
    label_pattern,
    ocr_data,
    value_pattern,
    max_vertical_gap=250,
    max_horizontal_gap=900,
):
    """
    Find a value OCR row spatially associated with a
    declaration label.

    Supports two common layouts:

    1. Horizontal:
           LABEL:  VALUE

    2. Vertical:
           LABEL:
           VALUE

    The candidate must:
      - match the supplied value pattern;
      - be spatially close to the label;
      - preferably appear to the right or below the label.

    Candidates are ranked using spatial distance and OCR confidence.
    """

    if not label_pattern or ocr_data is None:
        return None

    if getattr(ocr_data, "empty", True):
        return None

    label_text = label_pattern.group(0)

    label_evidence = _find_evidence(
        label_text,
        ocr_data,
    )

    if not label_evidence:
        return None

    label_bbox = label_evidence["bbox"]

    label_left = label_bbox["x1"]
    label_right = label_bbox["x2"]
    label_top = label_bbox["y1"]
    label_bottom = label_bbox["y2"]

    label_center_x = (
        label_left + label_right
    ) / 2

    label_center_y = (
        label_top + label_bottom
    ) / 2

    candidates = []

    for _, row in ocr_data.iterrows():

        candidate_text = str(
            row.get("text", "")
        ).strip()

        if not candidate_text:
            continue

        match = re.fullmatch(
            rf"\s*({value_pattern})\s*",
            candidate_text,
            re.IGNORECASE,
        )

        if not match:
            continue

        try:
            left = int(row["left"])
            top = int(row["top"])
            right = int(row["right"])
            bottom = int(row["bottom"])
            confidence = float(row["conf"])

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

        center_x = (
            left + right
        ) / 2

        center_y = (
            top + bottom
        ) / 2

        horizontal_gap = max(
            0,
            left - label_right,
        )

        vertical_gap = max(
            0,
            top - label_bottom,
        )

        # Candidate to the right of the label.
        is_right_candidate = (
            left >= label_right
            and abs(center_y - label_center_y)
            <= max_vertical_gap
            and horizontal_gap
            <= max_horizontal_gap
        )

        # Candidate below the label.
        is_below_candidate = (
            top >= label_bottom
            and abs(center_x - label_center_x)
            <= max_horizontal_gap
            and vertical_gap
            <= max_vertical_gap
        )

        if not (
            is_right_candidate
            or is_below_candidate
        ):
            continue

        if is_right_candidate:
            distance = (
                abs(center_y - label_center_y)
                + horizontal_gap * 0.25
            )
            layout_priority = 0

        else:
            distance = (
                abs(center_x - label_center_x)
                + vertical_gap * 0.25
            )
            layout_priority = 1

        candidates.append(
            (
                layout_priority,
                distance,
                -confidence,
                {
                    "text": match.group(1),
                    "confidence": confidence,
                    "bbox": {
                        "x1": left,
                        "y1": top,
                        "x2": right,
                        "y2": bottom,
                    },
                },
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[2],
        )
    )

    return candidates[0][3]

def _result(pattern, ocr_data=None):
    """
    Convert a regex match into the standard extractor result.
    """
    matched_text = (
        pattern.group(0)
        if pattern
        else None
    )

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
    with explicit net-quantity wording.

    Supports both:

        Net Weight: 400 g

    and OCR layouts where the label and value are detected
    as separate spatially related OCR rows.

    Serving size values are deliberately not accepted
    as net quantity.
    """

    text = text or ""

    # --------------------------------------------------------
    # 1. Explicit same-line net quantity
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 2. Find net-quantity label
    # --------------------------------------------------------

    label_pattern = _search(
        r"(net\s*(?:weight|quantity|qty))",
        text,
    )

    if label_pattern:

        # ----------------------------------------------------
        # Try spatially associated value from OCR
        # ----------------------------------------------------

        nearby_value = _find_nearby_value(
            label_pattern,
            ocr_data,
            r"\b\d+(?:\.\d+)?\s*"
            r"(?:g|gm|gms|kg|ml|l|litre|liter|ltr|pcs|pieces|n)\b",
        )

        if nearby_value:
            return {
                "detected": True,
                "matched_text": (
                    label_pattern.group(0)
                    + " "
                    + nearby_value["text"]
                ),
                "evidence": nearby_value,
            }

        # ----------------------------------------------------
        # Label exists but value was not detected
        # ----------------------------------------------------

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

    # --------------------------------------------------------
    # 3. Do NOT fall back to arbitrary quantities
    # --------------------------------------------------------

    return {
        "detected": False,
        "matched_text": None,
    }

def extract_manufacture_date(text, ocr_data=None):
    """
    Detect month/year of manufacture or packing.

    Supports labels such as:
        MFD
        MFG
        MFG DATE
        MANUFACTURED
        PKD
        PACKED
        DATE OF PACKAGING

    The associated value must be a date-like OCR token.
    Spatial matching supports both nearby horizontal
    and vertically separated layouts.
    """

    text = text or ""

    date_regex = (
        r"(?:"
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        r"|"
        r"\d{1,2}[/-][A-Za-z]{3,9}[/-]\d{2,4}"
        r"|"
        r"[A-Za-z]{3,9}[/-]\d{2,4}"
        r"|"
        r"\d{1,2}[A-Za-z]{3,9}\d{2,4}"
        r")"
    )

    label_pattern = _search(
        r"(?:"
        r"mfd|mfg(?:\.?\s*date)?|"
        r"manufactured|manufacture(?:d)?\s*date|"
        r"pkd|packed|date\s*of\s*packaging"
        r")",
        text,
    )

    if not label_pattern:
        return {
            "detected": False,
            "matched_text": None,
        }

    # First try same-text / same-row detection.
    contextual_pattern = _search(
        label_pattern.group(0)
        + r"\s*[:\-]?\s*"
        + "("
        + date_regex
        + ")",
        text,
    )

    if contextual_pattern:
        matched_text = contextual_pattern.group(0)

        result = {
            "detected": True,
            "matched_text": matched_text,
        }

        evidence = _find_evidence(
            contextual_pattern.group(1),
            ocr_data,
        )

        if evidence:
            result["evidence"] = evidence

        return result

    if ocr_data is not None and not getattr(
        ocr_data,
        "empty",
        True,
    ):
        label_evidence = _find_evidence(
            label_pattern.group(0),
            ocr_data,
        )

        if label_evidence:
            bbox = label_evidence["bbox"]

            label_left = bbox["x1"]
            label_right = bbox["x2"]
            label_top = bbox["y1"]
            label_bottom = bbox["y2"]

            label_center_x = (
                label_left + label_right
            ) / 2

            label_center_y = (
                label_top + label_bottom
            ) / 2

            candidates = []

            for _, row in ocr_data.iterrows():

                candidate_text = str(
                    row.get("text", "")
                ).strip()

                if not candidate_text:
                    continue

                match = re.fullmatch(
                    date_regex,
                    candidate_text,
                    re.IGNORECASE,
                )

                if not match:
                    continue

                try:
                    left = int(row["left"])
                    top = int(row["top"])
                    right = int(row["right"])
                    bottom = int(row["bottom"])
                    confidence = float(row["conf"])

                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ):
                    continue

                center_x = (
                    left + right
                ) / 2

                center_y = (
                    top + bottom
                ) / 2

                horizontal_gap = max(
                    0,
                    left - label_right,
                )

                vertical_gap = max(
                    0,
                    top - label_bottom,
                )

                # Horizontal layout.
                right_candidate = (
                    left >= label_right
                    and abs(
                    center_y - label_center_y
                    ) <= 300
                    and horizontal_gap <= 300
                )

                # Vertical layout.
                below_candidate = (
                    top >= label_bottom
                    and abs(
                    center_x - label_center_x
                    ) <= 900
                    and vertical_gap <= 700
                )

                if not (
                    right_candidate
                    or below_candidate
                ):
                    continue

                if right_candidate:
                    distance = (
                        abs(
                            center_y
                            - label_center_y
                    )
    + horizontal_gap * 2.0
)
                    priority = 0

                else:
                    distance = (
                        abs(
                            center_x
                            - label_center_x
                        )
                        + vertical_gap * 0.25
                    )
                    priority = 1

                candidates.append(
                    (
                        priority,
                        distance,
                        -confidence,
                        {
                            "text": candidate_text,
                            "confidence": confidence,
                            "bbox": {
                                "x1": left,
                                "y1": top,
                                "x2": right,
                                "y2": bottom,
                            },
                        },
                    )
                )

            if candidates:
                candidates.sort(
                    key=lambda item: (
                        item[0],
                        item[1],
                        item[2],
                    )
                )

                best = candidates[0][3]

                return {
                    "detected": True,
                    "matched_text": (
                        label_pattern.group(0)
                        + "\n"
                        + best["text"]
                    ),
                    "evidence": best,
                }

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



def extract_mrp(text, ocr_data=None):
    """
    Detect Maximum Retail Price (MRP).

    Strategy:
    1. Prefer MRP + value on the same OCR line.
    2. Otherwise search for a nearby monetary value.
    3. Reject dates, quantities, unit prices, nutrition values,
       and suspicious OCR fragments.
    4. If the MRP label is present but a reliable value cannot
       be associated with it, return REVIEW via value_missing.
    """

    text = text or ""

    # ---------------------------------------------------------
    # Patterns
    # ---------------------------------------------------------

    mrp_pattern = _search(
        r"\b(?:m\.?\s*r\.?\s*p\.?|mrp)\b",
        text,
    )

    money_pattern = re.compile(
        r"(?:₹|rs\.?|inr)?\s*"
        r"\d{1,5}(?:\.\d{1,2})?",
        re.IGNORECASE,
    )

    strict_money_pattern = re.compile(
        r"^(?:₹|rs\.?|inr)?\s*"
        r"\d{1,5}(?:\.\d{1,2})?$",
        re.IGNORECASE,
    )

    date_pattern = re.compile(
        r"^\d{1,4}"
        r"(?:[\/\-.]\d{1,2})"
        r"(?:[\/\-.]\d{1,4})$"
    )

    unit_pattern = re.compile(
        r"\b(?:g|gm|gms|kg|mg|ml|l|ltr|litre|liter)\b",
        re.IGNORECASE,
    )

    unit_price_pattern = re.compile(
        r"(?:₹|rs\.?|inr)?\s*\d+(?:\.\d{1,2})?\s*/\s*"
        r"(?:g|kg|ml|l|unit|piece|pc)\b",
        re.IGNORECASE,
    )

    # ---------------------------------------------------------
    # No MRP label
    # ---------------------------------------------------------

    if not mrp_pattern:
        return {
            "detected": False,
            "matched_text": None,
        }

    # ---------------------------------------------------------
    # Helper: validate candidate
    # ---------------------------------------------------------

    def clean_candidate(value):
        value = str(value).strip()

        # Remove common currency prefixes
        value = re.sub(
            r"^(?:₹|rs\.?|inr)\s*",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = value.strip(" :.-")

        if not value:
            return None

        # Reject dates
        if date_pattern.fullmatch(value):
            return None

        # Reject obvious unit prices
        if unit_price_pattern.search(value):
            return None

        # Reject quantities
        if unit_pattern.search(value):
            return None

        # Must be a clean monetary number
        if not re.fullmatch(
            r"\d{1,5}(?:\.\d{1,2})?",
            value,
        ):
            return None

        try:
            number = float(value)
        except ValueError:
            return None

        # MRP should be positive
        if number <= 0:
            return None

        return value

    # ---------------------------------------------------------
    # 1. Same-line MRP + value
    # ---------------------------------------------------------

    for line in text.splitlines():

        if not re.search(
            r"\b(?:m\.?\s*r\.?\s*p\.?|mrp)\b",
            line,
            re.IGNORECASE,
        ):
            continue

        # Avoid treating dates as MRP values
        candidates = money_pattern.findall(line)

        for candidate in candidates:

            cleaned = clean_candidate(candidate)

            if not cleaned:
                continue

            # Prevent extracting a partial number from
            # suspicious OCR fragments such as:
            # "1 42.00(0 6"
            suspicious_fragment = re.search(
                r"\d+\s+\d+\.\d+",
                line,
            )

            if suspicious_fragment:
                continue

            return {
                "detected": True,
                "matched_text": f"MRP {cleaned}",
                "evidence": _find_evidence(
                    candidate,
                    ocr_data,
                ),
            }

    # ---------------------------------------------------------
    # 2. Spatial OCR search
    # ---------------------------------------------------------

    if ocr_data is None:
        return {
            "detected": True,
            "matched_text": mrp_pattern.group(0),
            "value_missing": True,
        }

    rows = ocr_data.copy()

    if rows.empty:
        return {
            "detected": True,
            "matched_text": mrp_pattern.group(0),
            "value_missing": True,
        }

    # Locate OCR rows containing MRP
    label_rows = rows[
        rows["text"].astype(str).str.contains(
            r"\b(?:m\.?\s*r\.?\s*p\.?|mrp)\b",
            case=False,
            regex=True,
            na=False,
        )
    ]

    candidates = []

    for _, label in label_rows.iterrows():

        label_text = str(label["text"]).strip()

        # Ignore OCR rows where MRP appears as part of
        # another unrelated word.
        if not re.search(
            r"\b(?:m\.?\s*r\.?\s*p\.?|mrp)\b",
            label_text,
            re.IGNORECASE,
        ):
            continue

        label_left = float(label["left"])
        label_top = float(label["top"])
        label_right = float(label["right"])
        label_bottom = float(label["bottom"])

        label_cx = (label_left + label_right) / 2
        label_cy = (label_top + label_bottom) / 2

        for _, row in rows.iterrows():

            candidate_text = str(row["text"]).strip()

            if not candidate_text:
                continue

            # Do not compare the MRP label against itself
            if row.name == label.name:
                continue

            # -------------------------------------------------
            # Extract only clean monetary-looking candidates
            # -------------------------------------------------

            raw_candidates = money_pattern.findall(
                candidate_text
            )

            for raw_candidate in raw_candidates:

                cleaned = clean_candidate(raw_candidate)

                if not cleaned:
                    continue

                # If the complete OCR token contains unrelated
                # characters around the number, be conservative.
                #
                # Example:
                # "1 42.00(0 6"
                #
                # We do not trust "42.00" extracted from this.
                if not strict_money_pattern.fullmatch(
                    candidate_text
                ):
                    # Allow simple currency prefixes / punctuation
                    simplified = candidate_text.strip(
                        " :₹"
                    )

                    if not strict_money_pattern.fullmatch(
                        simplified
                    ):
                        continue

                candidate_left = float(row["left"])
                candidate_top = float(row["top"])
                candidate_right = float(row["right"])
                candidate_bottom = float(row["bottom"])

                candidate_cx = (
                    candidate_left + candidate_right
                ) / 2

                candidate_cy = (
                    candidate_top + candidate_bottom
                ) / 2

                # -------------------------------------------------
                # Horizontal candidate:
                # MRP  →  50.00
                # -------------------------------------------------

                horizontal_gap = (
                    candidate_left - label_right
                )

                vertical_diff = abs(
                    candidate_cy - label_cy
                )

                if (
                    horizontal_gap >= 0
                    and horizontal_gap <= 350
                    and vertical_diff <= 250
                ):
                    distance = (
                        horizontal_gap
                        + vertical_diff
                    )

                    candidates.append(
                        (
                            0,
                            distance,
                            float(row.get("conf", 0)),
                            cleaned,
                            row,
                        )
                    )

                # -------------------------------------------------
                # Vertical candidate:
                # MRP
                # 50.00
                # -------------------------------------------------

                vertical_gap = (
                    candidate_top - label_bottom
                )

                horizontal_diff = abs(
                    candidate_cx - label_cx
                )

                if (
                    vertical_gap >= 0
                    and vertical_gap <= 350
                    and horizontal_diff <= 250
                ):
                    distance = (
                        vertical_gap
                        + horizontal_diff
                    )

                    candidates.append(
                        (
                            1,
                            distance,
                            float(row.get("conf", 0)),
                            cleaned,
                            row,
                        )
                    )

    # ---------------------------------------------------------
    # 3. Select strongest spatial candidate
    # ---------------------------------------------------------

    if candidates:

        candidates.sort(
            key=lambda x: (
                x[0],
                x[1],
                -x[2],
            )
        )

        _, _, confidence, value, row = candidates[0]

        evidence = {
            "text": str(row["text"]),
            "confidence": confidence,
            "bbox": {
                "x1": int(row["left"]),
                "y1": int(row["top"]),
                "x2": int(row["right"]),
                "y2": int(row["bottom"]),
            },
        }

        return {
            "detected": True,
            "matched_text": f"MRP {value}",
            "evidence": evidence,
        }

    # ---------------------------------------------------------
    # 4. MRP label found, but value cannot be trusted
    # ---------------------------------------------------------

    evidence = _find_evidence(
        mrp_pattern.group(0),
        ocr_data,
    )

    result = {
        "detected": True,
        "matched_text": mrp_pattern.group(0),
        "value_missing": True,
    }

    if evidence:
        result["evidence"] = evidence

    return result


    
def extract_consumer_care(text, ocr_data=None):
    """
    Detect consumer-care / complaint contact information.

    Supports common package declarations such as:
        Consumer Care
        Customer Care
        Consumer Complaints
        Customer Service
        Toll Free
        Helpline
        Contact Us
        Call Us
        Write To
        Email Us

    Also detects email addresses and Indian toll-free /
    customer-care phone numbers.

    OCR evidence is attached when available.
    """

    text = text or ""

    # ---------------------------------------------------------
    # 1. Explicit consumer/customer care wording
    # ---------------------------------------------------------

    care_pattern = _search(
        r"(consumer\s+care|customer\s+care|"
        r"consumer\s+complaints?|customer\s+complaints?|"
        r"customer\s+service|consumer\s+service)",
        text,
    )

    # ---------------------------------------------------------
    # 2. Contact / complaint instructions
    # ---------------------------------------------------------

    complaint_pattern = _search(
        r"(?:in\s+case\s+of\s+any\s+)?"
        r"(?:complaint|complaints)",
        text,
    )

    contact_pattern = _search(
        r"(write\s+to|contact\s+us|reach\s+us|"
        r"email\s+us|call\s+us|write\s+us)",
        text,
    )

    # ---------------------------------------------------------
    # 3. Toll-free / helpline wording
    # ---------------------------------------------------------

    tollfree_pattern = _search(
        r"(toll[\s\-]*free|"
        r"helpline|"
        r"help\s*line|"
        r"hotline)",
        text,
    )

    # ---------------------------------------------------------
    # 4. Email address
    # ---------------------------------------------------------

    email_pattern = _search(
        r"\b[a-z0-9._%+\-]+"
        r"@[a-z0-9.\-]+\.[a-z]{2,}\b",
        text,
    )

    # ---------------------------------------------------------
    # 5. Indian customer-care / toll-free phone number
    # ---------------------------------------------------------

    phone_pattern = _search(
        r"\b(?:1800|1860)"
        r"[\s\-]?"
        r"\d{2,4}"
        r"[\s\-]?"
        r"\d{3,4}\b",
        text,
    )

    # ---------------------------------------------------------
    # 6. Select strongest evidence
    # ---------------------------------------------------------

    patterns = [
        care_pattern,
        complaint_pattern,
        contact_pattern,
        tollfree_pattern,
        email_pattern,
        phone_pattern,
    ]

    matched = next(
        (
            pattern
            for pattern in patterns
            if pattern
        ),
        None,
    )

    # ---------------------------------------------------------
    # 7. Build result
    # ---------------------------------------------------------

    result = {
        "detected": matched is not None,
        "matched_text": (
            matched.group(0)
            if matched
            else None
        ),
    }

    # ---------------------------------------------------------
    # 8. Attach OCR evidence
    # ---------------------------------------------------------

    if matched:
        evidence = _find_evidence(
            matched.group(0),
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