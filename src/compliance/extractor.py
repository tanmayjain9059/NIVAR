"""
Extraction of Legal Metrology declarations from OCR text.
"""

import re


def _search(pattern, text, flags=re.IGNORECASE):
    """
    Return the first regex match or None.
    """

    return re.search(pattern, text, flags)


def extract_manufacturer(text):
    pattern = _search(
        r"(manufactured|packed|marketed|imported)\s+by",
        text,
    )

    return {
        "detected": bool(pattern),
        "matched_text": pattern.group(0) if pattern else None,
    }


def extract_net_quantity(text):
    pattern = _search(
        r"\b\d+(\.\d+)?\s*"
        r"(g|gm|gms|kg|ml|l|litre|liter|ltr|pcs|pieces|n\b)",
        text,
    )

    return {
        "detected": bool(pattern),
        "matched_text": pattern.group(0) if pattern else None,
    }


def extract_manufacture_date(text):
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

    return {
        "detected": bool(pattern),
        "matched_text": pattern.group(0) if pattern else None,
    }


def extract_mrp(text):
    pattern = _search(
        r"(mrp|m\.r\.p|retail sale price)"
        r"\D{0,10}"
        r"\d+(\.\d+)?",
        text,
    )

    return {
        "detected": bool(pattern),
        "matched_text": pattern.group(0) if pattern else None,
    }


def extract_consumer_care(text):
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
        matched = email_pattern.group(0)
    elif phone_pattern:
        matched = phone_pattern.group(0)

    return {
        "detected": bool(email_pattern or phone_pattern),
        "matched_text": matched,
    }


def extract_country_of_origin(text):
    pattern = _search(
        r"(country of origin|made in)"
        r"\D{0,20}[a-z]+",
        text,
    )

    return {
        "detected": bool(pattern),
        "matched_text": pattern.group(0) if pattern else None,
        "conditional": True,
    }


def extract_declarations(raw_text, compliance_text=None):
    """
    Extract all currently supported declarations.

    The focused compliance OCR is searched first by placing it
    before the full-page OCR text.
    """

    if compliance_text:
        text = (
            f"{compliance_text}\n"
            f"{raw_text or ''}"
        )
    else:
        text = raw_text or ""

    return {
        "manufacturer_packer_importer": extract_manufacturer(text),
        "net_quantity": extract_net_quantity(text),
        "manufacture_date": extract_manufacture_date(text),
        "mrp": extract_mrp(text),
        "consumer_care": extract_consumer_care(text),
        "country_of_origin": extract_country_of_origin(text),
    }
