"""
Nutrition table extraction from packaged-food labels.
"""

import re


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


def _clean_text(text):
    return re.sub(
        r"[^a-z]",
        "",
        str(text).lower(),
    )


def _is_number_line(text):
    """
    Return numeric values if the line represents a
    nutrition value rather than a percentage/RDA line.
    """

    text = str(text).strip()

    # Ignore percentage lines such as:
    # 3%
    # 10%
    # 5%
    if "%" in text:
        return []

    matches = re.findall(
        r"(?<![a-zA-Z])\d+(?:\.\d+)?",
        text,
    )

    return [
        float(value)
        for value in matches
    ]


def parse_nutrition_text(text):
    """
    Parse nutrition values directly from already extracted OCR text.

    No additional OCR is performed here.
    """

    if not text:
        return {}

    lines = [
        line.strip()
        for line in str(text).splitlines()
        if line.strip()
    ]

    results = {}

    # Process the OCR output row-by-row.
    for index, line in enumerate(lines):

        cleaned_line = _clean_text(line)

        matched_nutrient = None

        # IMPORTANT:
        # Check longer/more specific nutrient names first.
        # Otherwise "Total Fat" could interfere with
        # "Saturated Fat" etc.
        ordered_nutrients = sorted(
            NUTRIENTS,
            key=lambda item: len(_clean_text(item)),
            reverse=True,
        )

        for nutrient in ordered_nutrients:

            target = _clean_text(nutrient)

            if cleaned_line == target:
                matched_nutrient = nutrient
                break

            # Handle labels such as:
            # Energy(kcal)
            # Total Fat (g)
            # Cholesterol (mg)
            if cleaned_line.startswith(target):

                remainder = cleaned_line[len(target):]

                if remainder in (
                    "",
                    "g",
                    "mg",
                    "kcal",
                    "g100g",
                    "mg100g",
                ) or (
                    "g" in remainder
                    or "mg" in remainder
                    or "kcal" in remainder
                ):
                    matched_nutrient = nutrient
                    break

        if matched_nutrient is None:
            continue

        # ----------------------------------------------------
        # Look for value on the same line first.
        # ----------------------------------------------------

        values = _is_number_line(line)

        # For labels such as "Energy(kcal)", the number
        # normally isn't on the same line.
        values = [
            value
            for value in values
            if value >= 0
        ]

        value = None

        # ----------------------------------------------------
        # Value is normally on the next OCR line.
        # ----------------------------------------------------

        if not values:

            for next_index in range(
                index + 1,
                min(index + 3, len(lines)),
            ):

                candidate_line = lines[next_index]

                # Never cross into another nutrient row.
                candidate_cleaned = _clean_text(
                    candidate_line
                )

                is_another_nutrient = any(
                    candidate_cleaned == _clean_text(other)
                    or candidate_cleaned.startswith(
                        _clean_text(other)
                    )
                    for other in NUTRIENTS
                    if other != matched_nutrient
                )

                if is_another_nutrient:
                    break

                candidate_values = _is_number_line(
                    candidate_line
                )

                if candidate_values:
                    value = candidate_values[0]
                    break

        else:
            value = values[0]

        if value is None:
            continue

        # ----------------------------------------------------
        # Units
        # ----------------------------------------------------

        if matched_nutrient == "Energy":
            unit = "kcal"

        elif matched_nutrient in (
            "Sodium",
            "Cholesterol",
        ):
            unit = "mg"

        else:
            unit = "g"

        results[matched_nutrient] = {
            "value": value,
            "unit": unit,
        }

    return results


def parse_nutrition_table(roi, config):
    """
    Backward-compatible Tesseract implementation.

    PaddleOCR should use parse_nutrition_text() instead.
    """

    if roi is None:
        return {}

    import pytesseract

    from src.ocr.preprocessing import prepare_roi_for_ocr

    cleaned = prepare_roi_for_ocr(
        roi,
        config,
    )

    text = pytesseract.image_to_string(
        cleaned,
        config=config["roi_ocr_config"],
    )

    return parse_nutrition_text(text)