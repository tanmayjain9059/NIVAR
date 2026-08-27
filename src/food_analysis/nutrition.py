"""
Nutrition table extraction from packaged-food labels.
"""

import re

import pytesseract

from src.ocr.preprocessing import prepare_roi_for_ocr


NUTRIENTS = [
    "Energy",
    "Protein",
    "Carbohydrate",
    "Total Sugars",
    "Added Sugars",
    "Dietary Fiber",
    "Total Fat",
    "Saturated Fat",
    "Trans Fat",
    "Cholesterol",
    "Sodium",
]


def parse_nutrition_table(roi, config):
    """
    OCR and parse a cropped nutrition table.

    This is an OCR-based heuristic parser. Values should be
    manually verified before being treated as authoritative.
    """

    if roi is None:
        return {}

    cleaned = prepare_roi_for_ocr(
        roi,
        config,
    )

    data = pytesseract.image_to_data(
        cleaned,
        config=config["roi_ocr_config"],
        output_type=pytesseract.Output.DATAFRAME,
    )

    data = data.dropna(subset=["text"])

    data["text"] = (
        data["text"]
        .astype(str)
        .str.strip()
    )

    data = data[data["text"] != ""].copy()

    for col in ("left", "top", "width", "height"):
        data[col] = data[col].astype(int)

    number_tokens = []

    for _, row in data.iterrows():

        for number in re.findall(
            r"\d+(?:\.\d+)?",
            str(row["text"]),
        ):

            try:
                value = float(number)
            except ValueError:
                continue

            number_tokens.append(
                {
                    "value": value,
                    "x": int(row["left"]),
                    "y": int(row["top"]),
                    "right": int(row["left"]) + int(row["width"]),
                    "bottom": int(row["top"]) + int(row["height"]),
                }
            )

    results = {}

    for nutrient in NUTRIENTS:

        target = re.sub(
            r"[^a-z]",
            "",
            nutrient.lower(),
        )

        matches = [
            row
            for _, row in data.iterrows()
            if target
            in re.sub(
                r"[^a-z]",
                "",
                str(row["text"]).lower(),
            )
        ]

        if not matches:
            continue

        nutrient_row = matches[0]

        nutrient_y = int(
            nutrient_row["top"]
        )

        nutrient_right = (
            int(nutrient_row["left"])
            + int(nutrient_row["width"])
        )

        candidates = []

        for number in number_tokens:

            vertical_distance = abs(
                number["y"] - nutrient_y
            )

            if (
                vertical_distance
                > config["nutrient_vertical_tolerance"]
            ):
                continue

            if number["x"] <= nutrient_right:
                continue

            horizontal_distance = (
                number["x"] - nutrient_right
            )

            if (
                horizontal_distance
                > config["nutrient_horizontal_max"]
            ):
                continue

            score = (
                vertical_distance * 3
                + horizontal_distance
            )

            candidates.append(
                {
                    "value": number["value"],
                    "score": score,
                }
            )

        if not candidates:
            continue

        candidates.sort(
            key=lambda item: item["score"]
        )

        best = candidates[0]

        if (
            best["score"]
            > config["nutrient_score_threshold"]
        ):
            continue

        if nutrient == "Energy":
            unit = "kcal"

        elif nutrient in (
            "Sodium",
            "Cholesterol",
        ):
            unit = "mg"

        else:
            unit = "g"

        results[nutrient] = {
            "value": best["value"],
            "unit": unit,
        }

    return results
