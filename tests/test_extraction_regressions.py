import pandas as pd

from src.compliance.validator import validate_declarations
from src.food_analysis.allergens import parse_allergens
from src.food_analysis.ingredients import parse_ingredients
from src.food_analysis.nutrition import parse_nutrition_text
from src.ocr.engine import extract_text_from_region
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
        "ACME\nPremium Basmati Rice\nManufactured by ABC Foods Pvt Ltd",
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
        "ABC Foods Pvt Ltd\nPlot 12 Industrial Area Hyderabad\nEnergy 412 kcal\nProtein 9 g",
        ocr_data=ocr,
    )
    assert result["product_name"] is None


def test_ingredient_parser_does_not_absorb_marketing_copy():
    text = (
        "INGREDIENTS: Refined Wheat Flour (Maida) (46%), "
        "Hydrogenated Vegetable Oils (Palm, Soyabean, Sunflower), "
        "Milk Solids, Refined Sugar, Butter, Whole Cumin (1.3%), "
        "Iodised Salt, Custard Powder, Natural Flavouring Substances "
        "(Cumin), Acidity Regulators (INS 503 (ii)) and Natural Flavouring "
        "Substances (Vanilla). Nutritional Information Energy 513 kcal"
    )
    result = parse_ingredients(text)
    assert any("Refined Wheat Flour" in item for item in result)
    assert any("Hydrogenated Vegetable Oils" in item for item in result)
    assert all("first bite" not in item.lower() for item in result)
    assert all("clinking" not in item.lower() for item in result)
    assert all("nutritional information" not in item.lower() for item in result)


def test_allergen_parser_only_returns_known_allergens():
    text = (
        "Allergen: Contains Wheat, Milk & Soy. "
        "May Contains Tree Nuts, Peanut, Sesame Seed & Mustard Seed. "
        "Added Sugars (g) 11"
    )
    contains, may = parse_allergens(text)
    assert contains == ["Wheat", "Milk", "Soy"]
    assert may == ["Tree Nuts", "Peanut", "Sesame", "Mustard"]


def test_region_extraction_preserves_spatial_boundaries():
    data = pd.DataFrame([
        {"text": "COOKIE HEAVEN", "left": 100, "top": 100, "right": 500, "bottom": 170, "width": 400, "height": 70, "conf": 0.95},
        {"text": "INGREDIENTS:", "left": 100, "top": 500, "right": 260, "bottom": 540, "width": 160, "height": 40, "conf": 0.95},
        {"text": "Flour (46%)", "left": 100, "top": 550, "right": 300, "bottom": 590, "width": 200, "height": 40, "conf": 0.95},
        {"text": "Nutritional Information", "left": 100, "top": 900, "right": 400, "bottom": 940, "width": 300, "height": 40, "conf": 0.95},
    ])
    region = {"x": 80, "y": 480, "w": 400, "h": 300}
    text = extract_text_from_region(data, region)
    assert text.splitlines() == ["INGREDIENTS:", "Flour (46%)"]


def test_food_parsers_are_section_scoped():
    ingredient_section = "INGREDIENTS: Wheat Flour, Sugar, Salt"
    allergen_section = "Allergen: Contains Wheat, Milk"
    unrelated_global_text = (
        "The clinking of chai cups and the crunch of snacktime\n"
        "The finest cookies for sharing with your loved ones.\n"
        "May contain The clinking of chai cups"
    )

    assert parse_ingredients(ingredient_section) == [
        "Wheat Flour",
        "Sugar",
        "Salt",
    ]
    assert parse_allergens(allergen_section) == (
        ["Wheat", "Milk"],
        [],
    )
    assert unrelated_global_text not in ingredient_section
    assert unrelated_global_text not in allergen_section

def test_compliance_detects_split_ocr_boxes_for_all_five_declarations():
    ocr = pd.DataFrame([
        {"text": "Manufactured by", "left": 100, "top": 100, "right": 300, "bottom": 130, "conf": 0.96},
        {"text": "ABC Foods Pvt Ltd", "left": 320, "top": 100, "right": 600, "bottom": 130, "conf": 0.95},
        {"text": "Plot 12 Industrial Area Hyderabad 500001", "left": 100, "top": 140, "right": 600, "bottom": 170, "conf": 0.94},
        {"text": "Net Quantity", "left": 100, "top": 220, "right": 280, "bottom": 250, "conf": 0.96},
        {"text": "500 g", "left": 320, "top": 220, "right": 390, "bottom": 250, "conf": 0.95},
        {"text": "MFD", "left": 100, "top": 300, "right": 170, "bottom": 330, "conf": 0.96},
        {"text": "08/2026", "left": 320, "top": 300, "right": 410, "bottom": 330, "conf": 0.95},
        {"text": "MRP", "left": 100, "top": 380, "right": 160, "bottom": 410, "conf": 0.96},
        {"text": "₹120", "left": 320, "top": 380, "right": 380, "bottom": 410, "conf": 0.95},
        {"text": "Consumer Care", "left": 100, "top": 460, "right": 260, "bottom": 490, "conf": 0.96},
        {"text": "1800 123 4567", "left": 320, "top": 460, "right": 470, "bottom": 490, "conf": 0.95},
    ])
    result = validate_declarations("", "", ocr_data=ocr)
    checks = result["checks"]
    assert checks["manufacturer_packer_importer"]["status"] == "FOUND"
    assert checks["net_quantity"]["status"] == "FOUND"
    assert checks["manufacture_date"]["status"] == "FOUND"
    assert checks["mrp"]["status"] == "FOUND"
    assert checks["consumer_care"]["status"] == "FOUND"


def test_compliance_recovers_real_paddle_ocr_date_and_landline_variants():
    """Regression for OCR forms observed in real package scans."""
    ocr = pd.DataFrame([
        {"text": "Manufactured By", "left": 100, "top": 100, "right": 300, "bottom": 130, "conf": 0.99},
        {"text": "Zydus Wellness Limited", "left": 320, "top": 100, "right": 620, "bottom": 130, "conf": 0.98},
        {"text": "Scheme No. 63, Survey No. 536, Ahmedabad", "left": 100, "top": 140, "right": 620, "bottom": 170, "conf": 0.96},
        {"text": "NET WEIGHT", "left": 100, "top": 220, "right": 300, "bottom": 250, "conf": 0.98},
        {"text": "55 g", "left": 320, "top": 220, "right": 390, "bottom": 250, "conf": 0.97},
        {"text": "MFG. DATE", "left": 100, "top": 300, "right": 240, "bottom": 330, "conf": 0.98},
        {"text": "16/07/2026", "left": 320, "top": 300, "right": 470, "bottom": 330, "conf": 0.97},
        {"text": "MRP", "left": 100, "top": 380, "right": 160, "bottom": 410, "conf": 0.98},
        {"text": "50.00", "left": 320, "top": 380, "right": 390, "bottom": 410, "conf": 0.97},
        {"text": "For Consumer Complaint / Query / Feedback", "left": 100, "top": 460, "right": 520, "bottom": 490, "conf": 0.98},
        {"text": "0120-2400286", "left": 100, "top": 500, "right": 280, "bottom": 530, "conf": 0.97},
    ])
    result = validate_declarations("", "", ocr_data=ocr)
    checks = result["checks"]
    assert checks["manufacturer_packer_importer"]["status"] == "FOUND"
    assert checks["net_quantity"]["status"] == "FOUND"
    assert checks["manufacture_date"]["status"] == "FOUND"
    assert checks["mrp"]["status"] == "FOUND"
    assert checks["consumer_care"]["status"] == "FOUND"


def test_compliance_recovers_compact_month_date_from_ocr():
    ocr = pd.DataFrame([
        {"text": "MFG. DATE", "left": 100, "top": 100, "right": 240, "bottom": 130, "conf": 0.98},
        {"text": "27DEC2023", "left": 260, "top": 100, "right": 430, "bottom": 130, "conf": 0.97},
    ])
    result = validate_declarations("", "", ocr_data=ocr)
    assert result["checks"]["manufacture_date"]["status"] == "FOUND"


def test_compliance_reconstructs_split_paddle_ocr_line_tokens():
    """A declaration value may be emitted as several adjacent OCR boxes."""
    ocr = pd.DataFrame([
        {"text": "Marketed by:", "left": 100, "top": 100, "right": 220, "bottom": 130, "conf": 0.99},
        {"text": "Unibic Foods India Private Limited,", "left": 225, "top": 100, "right": 580, "bottom": 130, "conf": 0.98},
        {"text": "#13, 2nd Floor, HAL 2nd Stage, 100 Feet Road, Bengaluru - 560038", "left": 100, "top": 140, "right": 650, "bottom": 170, "conf": 0.97},
        {"text": "BISCUITS NET WEIGHT:", "left": 100, "top": 250, "right": 300, "bottom": 280, "conf": 0.98},
        {"text": "67.5", "left": 320, "top": 250, "right": 370, "bottom": 280, "conf": 0.98},
        {"text": "g", "left": 375, "top": 250, "right": 395, "bottom": 280, "conf": 0.98},
        {"text": "MRP", "left": 100, "top": 320, "right": 160, "bottom": 350, "conf": 0.98},
        {"text": "₹", "left": 320, "top": 320, "right": 340, "bottom": 350, "conf": 0.98},
        {"text": "60.00", "left": 345, "top": 320, "right": 410, "bottom": 350, "conf": 0.98},
        {"text": "MFG. DATE:", "left": 100, "top": 390, "right": 230, "bottom": 420, "conf": 0.98},
        {"text": "28/07/2026", "left": 320, "top": 390, "right": 450, "bottom": 420, "conf": 0.97},
        {"text": "For any feedback, please contact the Consumer Care Executive", "left": 100, "top": 500, "right": 650, "bottom": 530, "conf": 0.98},
        {"text": "Tel. No. +91 96061 22221", "left": 100, "top": 540, "right": 360, "bottom": 570, "conf": 0.98},
    ])

    result = validate_declarations("", "", ocr_data=ocr)
    checks = result["checks"]

    assert checks["manufacturer_packer_importer"]["status"] == "FOUND"
    assert checks["manufacturer_packer_importer"]["manufacturer_name"] == "Unibic Foods India Private Limited"
    assert checks["net_quantity"]["status"] == "FOUND"
    assert checks["manufacture_date"]["status"] == "FOUND"
    assert checks["mrp"]["status"] == "FOUND"
    assert checks["consumer_care"]["status"] == "FOUND"


def test_compliance_supports_month_year_manufacture_date():
    ocr = pd.DataFrame([
        {"text": "MFG. DATE", "left": 100, "top": 100, "right": 240, "bottom": 130, "conf": 0.98},
        {"text": "08/2026", "left": 260, "top": 100, "right": 360, "bottom": 130, "conf": 0.97},
    ])

    result = validate_declarations("", "", ocr_data=ocr)

    assert result["checks"]["manufacture_date"]["status"] == "FOUND"


def test_compliance_mrp_uses_declared_price_not_unit_price():
    text = "MRP (Inclusive of All Taxes) Rs 60.00 Rs 0.89 per g"

    result = validate_declarations(text)

    check = result["checks"]["mrp"]
    assert check["status"] == "FOUND"
    assert check["matched_text"].lower().find("60.00") >= 0
    assert "0.89" not in check["matched_text"]
