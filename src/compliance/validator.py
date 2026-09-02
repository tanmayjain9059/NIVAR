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


def validate_declarations(
    raw_text,
    compliance_text=None,
    ocr_data=None,
):
    """
    Run extraction and create a structured first-pass
    Legal Metrology compliance report.

    Status meanings:

        FOUND
            Declaration and required evidence detected.

        NOT_FOUND
            Declaration was not detected by OCR.

        REVIEW
            Declaration was detected, but available evidence
            is insufficient for automatic verification or
            requires semantic/manual verification.

    The system deliberately does not claim legal compliance.
    """

    # --------------------------------------------------------
    # Extract declarations
    # --------------------------------------------------------

    extracted = extract_declarations(
        raw_text,
        compliance_text,
        ocr_data=ocr_data,
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

        # A declaration label may be visible while its required
        # value is not detected. This requires manual review.
        if result.get("value_missing"):
            status = "REVIEW"

        elif result["detected"]:
            status = "FOUND"

        else:
            status = "NOT_FOUND"

        checks[key] = {
            "label": rule["label"],
            "detected": result["detected"],
            "matched_text": result["matched_text"],
            "status": status,
        }

        # Add OCR evidence when available.
        if result.get("evidence"):
            checks[key]["evidence"] = result["evidence"]

        # Explain why manual review is required.
        if result.get("value_missing"):
            checks[key]["note"] = (
                "Declaration label detected, but the "
                "required value was not detected. "
                "Manual verification required."
            )

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

            # Conditional declarations require contextual
            # verification because applicability depends
            # on the product.
            "status": (
                "FOUND"
                if result["detected"]
                else "REVIEW"
            ),
        }

        if result.get("evidence"):
            checks[key]["evidence"] = result["evidence"]

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

    # --------------------------------------------------------
    # Mandatory declaration summary
    # --------------------------------------------------------

    mandatory_keys = list(
        MANDATORY_DECLARATIONS.keys()
    )

    # Declarations for which we have enough evidence to
    # currently mark them as FOUND.
    verified_count = sum(
        1
        for key in mandatory_keys
        if checks[key]["status"] == "FOUND"
    )

    # Declarations requiring human/semantic review.
    review_count = sum(
        1
        for key in mandatory_keys
        if checks[key]["status"] == "REVIEW"
    )

    # Declarations not detected by OCR.
    missing_count = sum(
        1
        for key in mandatory_keys
        if checks[key]["status"] == "NOT_FOUND"
    )

    total = len(mandatory_keys)

    # --------------------------------------------------------
    # Overall screening status
    # --------------------------------------------------------
    #
    # Do NOT return PASS/FAIL yet.
    #
    # The current system does not completely verify:
    #
    #   - legal correctness
    #   - declaration placement
    #   - minimum font size
    #   - readability
    #   - all conditional requirements
    #
    # Therefore the overall result remains REVIEW.
    # --------------------------------------------------------

    overall_status = "REVIEW"

    # --------------------------------------------------------
    # Final structured report
    # --------------------------------------------------------

    return {
        "overall_status": overall_status,

        "checks": checks,

        # Number of mandatory declarations currently
        # supported by sufficient OCR evidence.
        "mandatory_declarations_detected": verified_count,

        # Total number of configured mandatory declarations.
        "mandatory_declarations_total": total,

        # Additional breakdown for Android/Web/dashboard.
        "mandatory_declarations_review": review_count,
        "mandatory_declarations_missing": missing_count,

        "disclaimer": DISCLAIMER,
    }