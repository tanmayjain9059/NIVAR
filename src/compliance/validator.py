"""
Legal Metrology compliance validation.

This module converts extracted declarations into a structured
first-pass compliance report.
"""

from .rules import (
    MANDATORY_DECLARATIONS,
    CONDITIONAL_DECLARATIONS,
    MANUAL_REVIEW_DECLARATIONS,
)
from .extractor import extract_declarations


DISCLAIMER = (
    "Automated OCR-based first-pass check. "
    "NOT DETECTED does not confirm absence on the physical "
    "package. Verify manually before making any compliance claim."
)


def validate_declarations(
    raw_text,
    compliance_text=None,
):
    """
    Run extraction and create a compliance report.

    Results are intentionally conservative:
      FOUND       -> declaration detected by OCR
      NOT_FOUND   -> declaration not detected
      REVIEW      -> requires manual/semantic verification
    """

    extracted = extract_declarations(
        raw_text,
        compliance_text,
    )

    checks = {}

    # --------------------------------------------------------
    # Mandatory declarations
    # --------------------------------------------------------

    for key, rule in MANDATORY_DECLARATIONS.items():

        result = extracted.get(
            key,
            {
                "detected": False,
                "matched_text": None,
            },
        )

        checks[key] = {
            "label": rule["label"],
            "detected": result["detected"],
            "matched_text": result["matched_text"],
            "status": (
                "FOUND"
                if result["detected"]
                else "NOT_FOUND"
            ),
        }

    # --------------------------------------------------------
    # Conditional declarations
    # --------------------------------------------------------

    for key, rule in CONDITIONAL_DECLARATIONS.items():

        result = extracted.get(
            key,
            {
                "detected": False,
                "matched_text": None,
            },
        )

        checks[key] = {
            "label": rule["label"],
            "detected": result["detected"],
            "matched_text": result["matched_text"],
            "conditional": True,
            "status": (
                "FOUND"
                if result["detected"]
                else "REVIEW"
            ),
        }

    # --------------------------------------------------------
    # Manual-review declarations
    # --------------------------------------------------------

    for key, rule in MANUAL_REVIEW_DECLARATIONS.items():

        checks[key] = {
            "label": rule["label"],
            "detected": None,
            "matched_text": None,
            "status": "REVIEW",
            "note": (
                "Requires product-name/semantic extraction "
                "and manual verification."
            ),
        }

    mandatory_keys = list(
        MANDATORY_DECLARATIONS.keys()
    )

    detected_count = sum(
        1
        for key in mandatory_keys
        if checks[key]["detected"]
    )

    total = len(mandatory_keys)

    if detected_count == total:
        overall_status = "PASS"
    elif detected_count == 0:
        overall_status = "FAIL"
    else:
        overall_status = "PARTIAL"

    return {
        "overall_status": overall_status,
        "checks": checks,
        "mandatory_declarations_detected": detected_count,
        "mandatory_declarations_total": total,
        "disclaimer": DISCLAIMER,
    }
