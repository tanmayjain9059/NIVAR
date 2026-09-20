"""
Cross-image product analysis fusion.

Combines independent image analyses into one product-level
analysis while preserving image provenance.
"""

from collections import defaultdict
from copy import deepcopy
from typing import Any


def _normalize(value: Any) -> str:
    return " ".join(
        str(value or "")
        .strip()
        .lower()
        .split()
    )


def _confidence(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _choose_identity(candidates):
    valid = [
        candidate
        for candidate in candidates
        if candidate.get("value")
    ]

    if not valid:
        return {
            "value": None,
            "confidence": None,
            "evidence": None,
        }

    grouped = defaultdict(list)

    for candidate in valid:
        grouped[
            _normalize(candidate["value"])
        ].append(candidate)

    ranked = []

    for normalized, group in grouped.items():
        strongest = max(
            group,
            key=lambda item: _confidence(
                item.get("confidence")
            ),
        )

        average_confidence = (
            sum(
                _confidence(
                    item.get("confidence")
                )
                for item in group
            )
            / len(group)
        )

        # Repeated agreement across images is useful evidence.
        agreement_bonus = min(
            0.10,
            (len(group) - 1) * 0.025,
        )

        ranked.append(
            {
                "value": strongest["value"],
                "confidence": min(
                    1.0,
                    average_confidence
                    + agreement_bonus,
                ),
                "evidence": strongest.get(
                    "evidence"
                ),
                "support_count": len(group),
                "normalized": normalized,
            }
        )

    ranked.sort(
        key=lambda item: (
            item["support_count"],
            item["confidence"],
        ),
        reverse=True,
    )

    return ranked[0]


def _merge_check_values(image_results):
    """
    Merge compliance checks by key.

    A field is considered FOUND when at least one image has
    supporting evidence. Conflicts are retained for review.
    """

    merged = {}

    keys = set()

    for result in image_results:
        compliance = result.get(
            "legal_metrology_compliance",
            {},
        )

        keys.update(
            compliance.get("checks", {}).keys()
        )

    for key in sorted(keys):
        candidates = []

        for result in image_results:
            compliance = result.get(
                "legal_metrology_compliance",
                {},
            )

            check = compliance.get(
                "checks",
                {},
            ).get(key)

            if check:
                item = deepcopy(check)
                item["_image_id"] = result.get(
                    "_image_id"
                )
                candidates.append(item)

        if not candidates:
            continue

        found = [
            item
            for item in candidates
            if item.get("status") == "FOUND"
        ]

        review = [
            item
            for item in candidates
            if item.get("status") == "REVIEW"
        ]

        missing = [
            item
            for item in candidates
            if item.get("status") == "NOT_FOUND"
        ]

        if found:
            selected = max(
                found,
                key=lambda item: _confidence(
                    item.get("evidence", {}).get(
                        "confidence"
                    )
                ),
            )

            merged[key] = deepcopy(selected)
            merged[key]["source_images"] = [
                item["_image_id"]
                for item in found
            ]

            if len(found) > 1:
                merged[key]["support_count"] = len(
                    found
                )

            continue

        if review:
            selected = review[0]
            merged[key] = deepcopy(selected)
            merged[key]["source_images"] = [
                item["_image_id"]
                for item in review
            ]
            continue

        selected = missing[0]
        merged[key] = deepcopy(selected)
        merged[key]["source_images"] = [
            item["_image_id"]
            for item in missing
        ]

    return merged


def _recalculate_overall(compliance):
    checks = compliance.get("checks", {})

    core_keys = (
        "manufacturer_packer_importer",
        "net_quantity",
        "manufacture_date",
        "mrp",
        "consumer_care",
    )

    statuses = [
        checks[key]["status"]
        for key in core_keys
        if key in checks
    ]

    missing = statuses.count("NOT_FOUND")
    review = statuses.count("REVIEW")
    found = statuses.count("FOUND")

    total = len(core_keys)

    if missing > 0:
        overall = "NON_COMPLIANT"
    elif review > 0:
        overall = "REVIEW"
    elif found == total:
        overall = "COMPLIANT"
    else:
        overall = "REVIEW"

    result = deepcopy(compliance)

    result["overall_status"] = overall
    result["mandatory_declarations_detected"] = found
    result["mandatory_declarations_total"] = total
    result["mandatory_declarations_review"] = review
    result["mandatory_declarations_missing"] = missing

    return result


def fuse_image_analyses(
    image_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Combine multiple image analyses into one product result.
    """

    if not image_results:
        raise ValueError(
            "At least one image analysis is required."
        )

    product_candidates = []
    brand_candidates = []

    for result in image_results:
        identity = result.get(
            "product_identity",
            {},
        )

        image_id = result.get(
            "_image_id"
        )

        if identity.get("product_name"):
            product_candidates.append(
                {
                    "value": identity["product_name"],
                    "confidence": identity.get(
                        "product_name_confidence"
                    ),
                    "evidence": {
                        **(
                            identity.get(
                                "product_name_evidence"
                            )
                            or {}
                        ),
                        "image_id": image_id,
                    },
                }
            )

        if identity.get("brand"):
            brand_candidates.append(
                {
                    "value": identity["brand"],
                    "confidence": identity.get(
                        "brand_confidence"
                    ),
                    "evidence": {
                        **(
                            identity.get(
                                "brand_evidence"
                            )
                            or {}
                        ),
                        "image_id": image_id,
                    },
                }
            )

    product_identity = _choose_identity(
        product_candidates
    )

    brand_identity = _choose_identity(
        brand_candidates
    )

    merged_compliance = _merge_check_values(
        image_results
    )

    compliance_sources = []

    for result in image_results:
        compliance = result.get(
            "legal_metrology_compliance"
        )

        if compliance:
            compliance_sources.append(
                compliance
            )

    base_compliance = (
        deepcopy(compliance_sources[0])
        if compliance_sources
        else {}
    )

    base_compliance["checks"] = merged_compliance

    final_compliance = _recalculate_overall(
        base_compliance
    )

    return {
        "product_name": product_identity["value"],
        "product_name_confidence": product_identity[
            "confidence"
        ],
        "product_name_evidence": product_identity[
            "evidence"
        ],
        "brand": brand_identity["value"],
        "brand_confidence": brand_identity[
            "confidence"
        ],
        "brand_evidence": brand_identity[
            "evidence"
        ],
        "images_analyzed": len(image_results),
        "images": [
            {
                "image_id": result.get(
                    "_image_id"
                ),
                "filename": result.get(
                    "_filename"
                ),
                "analysis": {
                    key: value
                    for key, value in result.items()
                    if not key.startswith("_")
                },
            }
            for result in image_results
        ],
        "legal_metrology_compliance": final_compliance,
        "fusion": {
            "strategy": "cross_image_evidence_fusion",
            "source_image_count": len(
                image_results
            ),
        },
    }