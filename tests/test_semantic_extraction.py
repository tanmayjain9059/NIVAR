import pandas as pd
from src.product_intelligence.identity import identify_product
from src.food_analysis.ingredients import parse_ingredients
from src.food_analysis.allergens import parse_allergens
from src.food_analysis.nutrition import parse_nutrition_text


def ocr(rows): return pd.DataFrame(rows)


def test_product_identity_rejects_noise_and_extracts_brand():
    data=ocr([
        {"text":"7 Grain Biscuit","conf":96,"left":50,"top":30,"right":500,"bottom":100},
        {"text":"Manufactured by Patanjali Foods Ltd. FSSAI Lic No 100...","conf":95,"left":50,"top":900,"right":900,"bottom":960},
        {"text":"Energy 450 kcal","conf":99,"left":50,"top":300,"right":400,"bottom":350},
    ])
    result=identify_product("7 Grain Biscuit Manufactured by Patanjali Foods Ltd.",data)
    assert result["product_name"]=="7 Grain Biscuit"
    assert result["brand"]=="Patanjali"


def test_ingredients_stop_before_nutrition():
    result=parse_ingredients("Ingredients: Wheat Flour, Sugar, Edible Vegetable Oil, Raising Agent (INS 500), Nutrition Information Energy 450 kcal")
    assert result[:3]==["Wheat Flour","Sugar","Edible Vegetable Oil"]
    assert not any("Energy" in x for x in result)


def test_allergens_are_bounded():
    contains,may=parse_allergens("Contains Wheat & Sulphite. Packed by Patanjali Foods. Customer Care 1800 123 456")
    assert contains==["Wheat","Sulphite"]
    assert may==[]


def test_nutrition_inline_and_percentage():
    result=parse_nutrition_text("Energy 450 kcal 23%\nProtein 7.5 g 12%\nSodium 220 mg 9%")
    assert result["Energy"]["value"]==450
    assert result["Protein"]["value"]==7.5
    assert result["Sodium"]["value"]==220
