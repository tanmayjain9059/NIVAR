"""
Legal Metrology compliance validation.

This module converts extracted declarations into a structured
first-pass compliance report.

Important:
This is an automated screening system and NOT a legal
compliance certification.
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


# These are the five core MVP declarations used for the
# overall compliance decision.
CORE_MANDATORY_KEYS = (
    "manufacturer_packer_importer",
    "net_quantity",
    "manufacture_date",
    "mrp",
    "consumer_care",
)


def validate_declarations(raw_text, compliance_text=None, ocr_data=None):
    extracted = extract_declarations(
        raw_text,
        compliance_text,
        ocr_data=ocr_data,
    )

    checks = {}

    # ------------------------------------------------------------
    # CORE MANDATORY DECLARATIONS
    # ------------------------------------------------------------
    for key in CORE_MANDATORY_KEYS:
        rule = MANDATORY_DECLARATIONS.get(
            key,
            {"label": key.replace("_", " ").title()},
        )

        result = extracted.get(
            key,
            {
                "detected": False,
                "matched_text": None,
            },
        )

        if result.get("value_missing"):
            status = "REVIEW"
        elif result.get("detected"):
            status = "FOUND"
        else:
            status = "NOT_FOUND"

        checks[key] = {
            "label": rule["label"],
            "detected": result.get("detected", False),
            "matched_text": result.get("matched_text"),
            "status": status,
        }

        if result.get("evidence"):
            checks[key]["evidence"] = result["evidence"]

        if result.get("value_missing"):
            checks[key]["note"] = (
                "Declaration label detected, but the required value "
                "was not detected. Manual verification required."
            )

    # ------------------------------------------------------------
    # OTHER MANDATORY DECLARATIONS FROM RULES
    #
    # These remain visible in the detailed report, but the five
    # core MVP declarations above control the overall MVP status.
    # ------------------------------------------------------------
    for key, rule in MANDATORY_DECLARATIONS.items():
        if key in CORE_MANDATORY_KEYS:
            continue

        result = extracted.get(
            key,
            {
                "detected": False,
                "matched_text": None,
            },
        )

        if result.get("value_missing"):
            status = "REVIEW"
        elif result.get("detected"):
            status = "FOUND"
        else:
            status = "NOT_FOUND"

        checks[key] = {
            "label": rule["label"],
            "detected": result.get("detected", False),
            "matched_text": result.get("matched_text"),
            "status": status,
        }

        if result.get("evidence"):
            checks[key]["evidence"] = result["evidence"]

        if result.get("value_missing"):
            checks[key]["note"] = (
                "Declaration label detected, but the required value "
                "was not detected. Manual verification required."
            )

    # ------------------------------------------------------------
    # CONDITIONAL DECLARATIONS
    # ------------------------------------------------------------
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
            "detected": result.get("detected", False),
            "matched_text": result.get("matched_text"),
            "conditional": True,
            "status": (
                "FOUND"
                if result.get("detected")
                else "REVIEW"
            ),
        }

        if result.get("evidence"):
            checks[key]["evidence"] = result["evidence"]

    # ------------------------------------------------------------
    # MANUAL-REVIEW DECLARATIONS
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # OVERALL MVP STATUS
    #
    # 5/5 FOUND       -> COMPLIANT
    # REVIEW present  -> REVIEW
    # NOT_FOUND       -> NON_COMPLIANT
    # ------------------------------------------------------------
    core_statuses = [
        checks[key]["status"]
        for key in CORE_MANDATORY_KEYS
    ]

    verified_count = core_statuses.count("FOUND")
    review_count = core_statuses.count("REVIEW")
    missing_count = core_statuses.count("NOT_FOUND")

    total = len(CORE_MANDATORY_KEYS)

    if missing_count > 0:
        overall_status = "NON_COMPLIANT"
    elif review_count > 0:
        overall_status = "REVIEW"
    elif verified_count == total:
        overall_status = "COMPLIANT"
    else:
        overall_status = "REVIEW"

    return {
        "overall_status": overall_status,
        "checks": checks,
        "mandatory_declarations_detected": verified_count,
        "mandatory_declarations_total": total,
        "mandatory_declarations_review": review_count,
        "mandatory_declarations_missing": missing_count,
        "disclaimer": DISCLAIMER,
    }