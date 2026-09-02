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


def _is_nutrient_label(text, nutrient):
    """
    Check whether an OCR text item represents a nutrient label.
    """

    cleaned_line = _clean_text(text)
    target = _clean_text(nutrient)

    if cleaned_line == target:
        return True

    if cleaned_line.startswith(target):

        remainder = cleaned_line[len(target):]

        if remainder in (
            "",
            "g",
            "mg",
            "kcal",
            "g100g",
            "mg100g",
        ):
            return True

        if (
            "g" in remainder
            or "mg" in remainder
            or "kcal" in remainder
        ):
            return True

    return False


def _get_unit(nutrient):
    """
    Return the standard unit used by our structured result.
    """

    if nutrient == "Energy":
        return "kcal"

    if nutrient in (
        "Sodium",
        "Cholesterol",
    ):
        return "mg"

    return "g"


def _extract_spatial_nutrition(ocr_data):
    """
    Extract nutrition values using OCR bounding boxes.

    A nutrient label is matched with the closest numeric OCR
    value on the same horizontal row.

    This prevents values from neighbouring rows being assigned
    to the wrong nutrient.
    """

    if ocr_data is None:
        return {}

    if getattr(ocr_data, "empty", True):
        return {}

    rows = []

    for _, row in ocr_data.iterrows():

        text = str(row.get("text", "")).strip()

        if not text:
            continue

        try:
            left = float(row["left"])
            top = float(row["top"])
            right = float(row["right"])
            bottom = float(row["bottom"])
            confidence = float(row["conf"])
        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

        rows.append(
            {
                "text": text,
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom,
                "center_x": (left + right) / 2,
                "center_y": (top + bottom) / 2,
                "confidence": confidence,
            }
        )

    if not rows:
        return {}

    results = {}

    ordered_nutrients = sorted(
        NUTRIENTS,
        key=lambda item: len(_clean_text(item)),
        reverse=True,
    )

    for nutrient in ordered_nutrients:

        labels = [
            row
            for row in rows
            if _is_nutrient_label(
                row["text"],
                nutrient,
            )
        ]

        if not labels:
            continue

        # Use the first occurrence of the nutrient.
        label = labels[0]

        candidates = []

        for row in rows:

            # The candidate must contain a numeric value.
            values = _is_number_line(row["text"])

            if not values:
                continue

            # Ignore percentages / RDA values.
            if "%" in row["text"]:
                continue

            # The value should normally be to the right
            # of the nutrient label.
            if row["left"] < label["right"] - 20:
                continue

            # Calculate vertical distance between the centres
            # of the nutrient label and candidate value.
            vertical_distance = abs(
                row["center_y"] - label["center_y"]
            )

            # Same-row values should be reasonably close.
            max_vertical_distance = max(
                120.0,
                (label["bottom"] - label["top"]) * 1.5,
            )

            if vertical_distance > max_vertical_distance:
                continue

            horizontal_distance = (
                row["left"] - label["right"]
            )

            candidates.append(
                (
                    vertical_distance,
                    horizontal_distance,
                    row,
                    values,
                )
            )

        if not candidates:
            continue

        # Prioritize same-row alignment first,
        # then horizontal proximity.
        candidates.sort(
            key=lambda item: (
                item[0],
                item[1],
            )
        )

        _, _, selected_row, values = candidates[0]

        results[nutrient] = {
            "value": values[0],
            "unit": _get_unit(nutrient),
        }

    return results


def parse_nutrition_text(text, ocr_data=None):
    """
    Parse nutrition values from OCR text.

    When PaddleOCR dataframe information is available,
    spatial extraction is preferred.

    The text-only implementation remains as a fallback
    for Tesseract and other callers.
    """

    if not text:
        return {}

    # --------------------------------------------------------
    # Prefer spatial OCR when available.
    # --------------------------------------------------------

    if ocr_data is not None:
        spatial_results = _extract_spatial_nutrition(
            ocr_data
        )

        if spatial_results:
            return spatial_results

    # --------------------------------------------------------
    # Existing text-based fallback.
    # --------------------------------------------------------

    lines = [
        line.strip()
        for line in str(text).splitlines()
        if line.strip()
    ]

    results = {}

    ordered_nutrients = sorted(
        NUTRIENTS,
        key=lambda item: len(_clean_text(item)),
        reverse=True,
    )

    for index, line in enumerate(lines):

        matched_nutrient = None

        for nutrient in ordered_nutrients:

            if _is_nutrient_label(
                line,
                nutrient,
            ):
                matched_nutrient = nutrient
                break

        if matched_nutrient is None:
            continue

        values = _is_number_line(line)

        values = [
            value
            for value in values
            if value >= 0
        ]

        value = None

        if not values:

            for next_index in range(
                index + 1,
                min(index + 3, len(lines)),
            ):

                candidate_line = lines[next_index]

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

        results[matched_nutrient] = {
            "value": value,
            "unit": _get_unit(
                matched_nutrient
            ),
        }

    return results


def parse_nutrition_table(roi, config):
    """
    Backward-compatible Tesseract implementation.

    PaddleOCR should use parse_nutrition_text().
    """

    if roi is None:
        return {}

    import pytesseract

    from src.ocr.preprocessing import (
        prepare_roi_for_ocr,
    )

    cleaned = prepare_roi_for_ocr(
        roi,
        config,
    )

    text = pytesseract.image_to_string(
        cleaned,
        config=config["roi_ocr_config"],
    )

    return parse_nutrition_text(text)