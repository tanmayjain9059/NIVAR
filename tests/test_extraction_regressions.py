import pandas as pd

from src.compliance.validator import validate_declarations
from src.food_analysis.nutrition import parse_nutrition_text
from src.product_intelligence.fusion import fuse_image_analyses


def test_nutrition_combines_spatial_and_text_recall():
    ocr = pd.DataFrame([
        {"text": "Energy", "left": 10, "top": 10, "width": 50, "height": 20, "right": 60, "bottom": 30, "conf": 95},
        {"text": "412", "left": 70, "top": 10, "width": 25, "height": 20, "right": 95, "bottom": 30, "conf": 95},
    ])
    result = parse_nutrition_text(
        "Energy 412 kcal\nProtein 9 g\nSodium 110 mg",
        ocr_data=ocr,
    )
    assert result["Energy"]["value"] == 412
    assert result["Protein"]["value"] == 9
    assert result["Sodium"]["value"] == 110


def test_compliance_same_line_values_are_preserved():
    text = (
        "Manufactured by ABC Foods Pvt Ltd\n"
        "Net Quantity 500 g\n"
        "Plot 12, Industrial Area, Hyderabad - 500001\n"
        "MFD 14/08/2026\n"
        "MRP ₹120\n"
        "Consumer Care 1800 123 4567"
    )
    result = validate_declarations(text)
    checks = result["checks"]
    for key in (
        "manufacturer_packer_importer",
        "net_quantity",
        "manufacture_date",
        "mrp",
        "consumer_care",
    ):
        assert checks[key]["status"] == "FOUND"
    assert checks["manufacturer_packer_importer"]["manufacturer_name"] == "ABC Foods Pvt Ltd"
    assert checks["manufacturer_packer_importer"]["address_detected"] is True


def test_multi_image_fusion_does_not_drop_food_fields():
    images = [
        {
            "_image_id": "OCR-1",
            "_filename": "front.jpg",
            "product_identity": {"product_name": "Sample", "product_name_confidence": 0.9},
            "ingredients": ["wheat flour", "sugar"],
            "allergens": {"contains": ["wheat"], "may_contain": []},
            "nutrition": {"Energy": {"value": 400, "unit": "kcal"}},
            "legal_metrology_compliance": {"checks": {}, "overall_status": "REVIEW"},
        },
        {
            "_image_id": "OCR-2",
            "_filename": "back.jpg",
            "product_identity": {"brand": "Sample Brand", "brand_confidence": 0.95},
            "ingredients": ["salt"],
            "allergens": {"contains": [], "may_contain": ["nuts"]},
            "nutrition": {"Protein": {"value": 8, "unit": "g"}},
            "legal_metrology_compliance": {"checks": {}, "overall_status": "REVIEW"},
        },
    ]
    result = fuse_image_analyses(images)
    assert result["ingredients"] == ["wheat flour", "sugar", "salt"]
    assert result["allergens"]["contains"] == ["wheat"]
    assert result["allergens"]["may_contain"] == ["nuts"]
    assert result["nutrition"]["Energy"]["value"] == 400
    assert result["nutrition"]["Protein"]["value"] == 8
    assert len(result["images"]) == 2


def test_manufacturer_selection_prefers_company_name_over_address():
    from src.compliance.enhanced_extractor import extract_declarations

    text = (
        "Manufactured by\n"
        "ABC Foods Pvt Ltd\n"
        "Plot 12, Industrial Area, Hyderabad - 500001\n"
        "Consumer Care 1800 123 4567"
    )
    result = extract_declarations(text)
    value = result["manufacturer_packer_importer"]["matched_text"]
    assert "ABC Foods Pvt Ltd" in value
    assert "Industrial Area" not in value


def test_product_name_prefers_explicit_food_name_over_brand_and_manufacturer():
    from src.product_intelligence.identity import identify_product

    ocr = pd.DataFrame([
        {"text": "ACME", "left": 100, "top": 40, "right": 260, "bottom": 100, "conf": 96},
        {"text": "Premium Basmati Rice", "left": 110, "top": 125, "right": 520, "bottom": 180, "conf": 94},
        {"text": "Manufactured by ABC Foods Pvt Ltd", "left": 100, "top": 1500, "right": 650, "bottom": 1540, "conf": 97},
        {"text": "Net Quantity 5 kg", "left": 100, "top": 1600, "right": 350, "bottom": 1640, "conf": 96},
    ])
    result = identify_product(
        "ACME\\nPremium Basmati Rice\\nManufactured by ABC Foods Pvt Ltd",
        ocr_data=ocr,
    )
    assert result["product_name"] == "Premium Basmati Rice"


def test_product_name_is_not_manufacturer_address_or_nutrition_noise():
    from src.product_intelligence.identity import identify_product

    ocr = pd.DataFrame([
        {"text": "ABC Foods Pvt Ltd", "left": 100, "top": 1400, "right": 400, "bottom": 1440, "conf": 98},
        {"text": "Plot 12 Industrial Area Hyderabad", "left": 100, "top": 1450, "right": 520, "bottom": 1490, "conf": 98},
        {"text": "Energy 412 kcal", "left": 100, "top": 900, "right": 350, "bottom": 940, "conf": 99},
        {"text": "Protein 9 g", "left": 100, "top": 950, "right": 300, "bottom": 990, "conf": 99},
    ])
    result = identify_product(
        "ABC Foods Pvt Ltd\\nPlot 12 Industrial Area Hyderabad\\nEnergy 412 kcal\\nProtein 9 g",
        ocr_data=ocr,
    )
    assert result["product_name"] is None
