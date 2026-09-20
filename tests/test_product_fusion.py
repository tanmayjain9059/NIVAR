from src.product_intelligence.fusion import fuse_image_analyses


CORE_KEYS = (
    "manufacturer_packer_importer",
    "net_quantity",
    "manufacture_date",
    "mrp",
    "consumer_care",
)


def make_check(status, value=None, confidence=0.9):
    check = {
        "label": "Test declaration",
        "detected": status == "FOUND",
        "matched_text": value,
        "status": status,
    }

    if value is not None:
        check["value"] = value

    check["evidence"] = {
        "text": value,
        "confidence": confidence,
        "bbox": {
            "x1": 10,
            "y1": 10,
            "x2": 200,
            "y2": 60,
        },
    }

    return check


def make_compliance(statuses=None, values=None):
    statuses = statuses or {}
    values = values or {}

    checks = {}

    for key in CORE_KEYS:
        checks[key] = make_check(
            status=statuses.get(key, "NOT_FOUND"),
            value=values.get(key),
        )

    return {
        "overall_status": "REVIEW",
        "checks": checks,
        "mandatory_declarations_detected": 0,
        "mandatory_declarations_total": 5,
        "mandatory_declarations_review": 0,
        "mandatory_declarations_missing": 5,
    }


def make_image(
    image_id,
    compliance,
    product_name="Premium Rice",
    brand="Test Brand",
):
    return {
        "_image_id": image_id,
        "_filename": f"{image_id}.jpg",
        "product_identity": {
            "product_name": product_name,
            "product_name_confidence": 0.90,
            "product_name_evidence": {
                "text": product_name,
                "confidence": 0.90,
                "bbox": {
                    "x1": 10,
                    "y1": 10,
                    "x2": 200,
                    "y2": 60,
                },
            },
            "brand": brand,
            "brand_confidence": 0.92,
            "brand_evidence": {
                "text": brand,
                "confidence": 0.92,
                "bbox": {
                    "x1": 10,
                    "y1": 70,
                    "x2": 200,
                    "y2": 120,
                },
            },
        },
        "legal_metrology_compliance": compliance,
    }


def test_all_five_core_declarations_found_is_compliant():
    statuses = {
        key: "FOUND"
        for key in CORE_KEYS
    }

    values = {
        key: f"value-{key}"
        for key in CORE_KEYS
    }

    result = fuse_image_analyses([
        make_image(
            "IMG-1",
            make_compliance(statuses, values),
        )
    ])

    compliance = result["legal_metrology_compliance"]

    assert compliance["overall_status"] == "COMPLIANT"
    assert compliance["mandatory_declarations_detected"] == 5
    assert compliance["mandatory_declarations_missing"] == 0
    assert compliance["mandatory_declarations_review"] == 0


def test_any_core_not_found_is_non_compliant():
    statuses = {
        key: "FOUND"
        for key in CORE_KEYS
    }

    statuses["mrp"] = "NOT_FOUND"

    result = fuse_image_analyses([
        make_image(
            "IMG-1",
            make_compliance(statuses),
        )
    ])

    compliance = result["legal_metrology_compliance"]

    assert compliance["overall_status"] == "NON_COMPLIANT"
    assert compliance["mandatory_declarations_missing"] == 1


def test_review_is_preserved():
    statuses = {
        key: "FOUND"
        for key in CORE_KEYS
    }

    statuses["mrp"] = "REVIEW"

    result = fuse_image_analyses([
        make_image(
            "IMG-1",
            make_compliance(statuses),
        )
    ])

    compliance = result["legal_metrology_compliance"]

    assert compliance["overall_status"] == "REVIEW"
    assert compliance["mandatory_declarations_review"] == 1


def test_found_on_second_image_is_fused():
    first_statuses = {
        key: "FOUND"
        for key in CORE_KEYS
    }
    first_statuses["mrp"] = "NOT_FOUND"

    second_statuses = {
        key: "FOUND"
        for key in CORE_KEYS
    }

    result = fuse_image_analyses([
        make_image(
            "IMG-FRONT",
            make_compliance(first_statuses),
        ),
        make_image(
            "IMG-BACK",
            make_compliance(
                second_statuses,
                {"mrp": "MRP ₹250"},
            ),
        ),
    ])

    compliance = result["legal_metrology_compliance"]

    assert compliance["overall_status"] == "COMPLIANT"
    assert compliance["checks"]["mrp"]["status"] == "FOUND"
    assert (
        "IMG-BACK"
        in compliance["checks"]["mrp"]["source_images"]
    )


def test_same_product_identity_is_fused():
    result = fuse_image_analyses([
        make_image(
            "IMG-1",
            make_compliance(),
            product_name="Premium Rice",
            brand="Fortune",
        ),
        make_image(
            "IMG-2",
            make_compliance(),
            product_name="Premium Rice",
            brand="Fortune",
        ),
    ])

    assert result["product_name"] == "Premium Rice"
    assert result["brand"] == "Fortune"
    assert result["images_analyzed"] == 2


def test_empty_input_is_rejected():
    try:
        fuse_image_analyses([])
    except ValueError as exc:
        assert "At least one image analysis" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for empty image analysis list"
        )
