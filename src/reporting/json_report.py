"""
JSON report generation for the food label analyzer.
"""

import json
from pathlib import Path


def build_structured_result(
    file_path,
    nutrition,
    ingredients,
    contains,
    may_contain,
    compliance_report,
    nutrients_total,
):
    return {
        "source_image": str(file_path),

        "legal_metrology_compliance": compliance_report,

        "brand": None,
        "product_name": None,

        "ingredients": ingredients,

        "allergens": {
            "contains": contains,
            "may_contain": may_contain,
        },

        "nutrition": {
            nutrient: {
                "value": item["value"],
                "unit": item["unit"],
            }
            for nutrient, item in nutrition.items()
        },

        "quantity": None,
        "manufacturer": None,
        "manufacturing_date": None,
        "expiry_date": None,

        "meta": {
            "nutrition_fields_found": len(nutrition),
            "nutrition_fields_total": nutrients_total,
            "ingredients_found": len(ingredients),
            "confirmed_allergens": len(contains),
            "possible_allergens": len(may_contain),
        },
    }


def save_json_result(
    result,
    source_image_path,
    output_dir="results",
):
    output_path = Path(output_dir)
    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    stem = Path(source_image_path).stem

    result_file = (
        output_path
        / f"{stem}_result.json"
    )

    with open(
        result_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"Structured result saved to: {result_file}"
    )

    return result_file
