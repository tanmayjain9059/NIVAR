"""
Geometry-first section detection for packaged-food labels.
"""

from .engine import clean_word


def _box(row):
    return {
        "x": int(row["left"]),
        "y": int(row["top"]),
        "w": int(row["width"]),
        "h": int(row["height"]),
    }


def _matches(data, tokens):
    matches = []

    if data is None or getattr(data, "empty", True):
        return matches

    for _, row in data.iterrows():
        word = clean_word(row.get("text", ""))

        if any(token in word for token in tokens):
            matches.append(row)

    return matches


def find_ingredients_heading(data):
    matches = _matches(data, ("ingredient", "composition"))
    return _box(matches[0]) if matches else None


def find_compliance_heading(data):
    matches = _matches(
        data,
        (
            "manufacturedby",
            "manufactured",
            "marketedby",
            "packedby",
            "packed",
            "mrp",
            "batch",
            "consumer",
            "customer",
        ),
    )
    return _box(matches[0]) if matches else None


def _region_from_anchor(
    image,
    anchor,
    config,
    left_key,
    top_key,
    right_key,
    height_key,
):
    x = max(0, anchor["x"] - config.get(left_key, 200))
    y = max(0, anchor["y"] - config.get(top_key, 80))
    right = min(
        image.shape[1],
        anchor["x"] + anchor["w"] + config.get(right_key, 1800),
    )
    bottom = min(
        image.shape[0],
        y + config.get(height_key, 1000),
    )

    if bottom <= y or right <= x:
        return None

    return {
        "x": x,
        "y": y,
        "w": right - x,
        "h": bottom - y,
    }


def detect_nutrition_region(image, data, config):
    matches = _matches(
        data,
        (
            "nutritional",
            "nutrition",
            "nutritionfacts",
            "nutritioninformation",
        ),
    )

    if not matches:
        return None

    anchor = min(
        matches,
        key=lambda row: int(row["top"]),
    )

    return _region_from_anchor(
        image,
        _box(anchor),
        config,
        "nutrition_left_padding",
        "nutrition_top_padding",
        "nutrition_right_padding",
        "nutrition_height",
    )


def detect_ingredients_region(
    image,
    data,
    nutrition_region,
    config,
):
    heading = find_ingredients_heading(data)

    if heading is None:
        return None

    region = _region_from_anchor(
        image,
        heading,
        config,
        "ingredients_left_padding",
        "ingredients_top_padding",
        "ingredients_right_padding",
        "ingredients_height",
    )

    if region is None:
        return None

    if nutrition_region and nutrition_region["y"] > region["y"]:
        region["h"] = max(
            1,
            min(
                region["h"],
                nutrition_region["y"]
                - region["y"]
                - config.get("section_gap", 30),
            ),
        )

    return region if region["h"] > 1 else None


def detect_allergen_region(image, data, config):
    matches = _matches(data, ("allergen",))

    if not matches:
        return None

    anchor = min(
        matches,
        key=lambda row: int(row["top"]),
    )

    return _region_from_anchor(
        image,
        _box(anchor),
        config,
        "allergen_left_padding",
        "allergen_top_padding",
        "allergen_right_padding",
        "allergen_height",
    )


def crop_region(image, region):
    if region is None:
        return None

    x = max(0, int(region["x"]))
    y = max(0, int(region["y"]))
    x2 = min(
        image.shape[1],
        x + int(region["w"]),
    )
    y2 = min(
        image.shape[0],
        y + int(region["h"]),
    )

    if x2 <= x or y2 <= y:
        return None

    return image[y:y2, x:x2]


def detect_compliance_region(image, data, config):
    heading = find_compliance_heading(data)

    if heading is None:
        return None

    return _region_from_anchor(
        image,
        heading,
        config,
        "compliance_left_padding",
        "compliance_top_padding",
        "compliance_right_padding",
        "compliance_height",
    )


def split_region_horizontally(region, ratio=0.5):
    if region is None:
        return None, None

    ratio = max(0.1, min(0.9, float(ratio)))
    left_width = int(region["w"] * ratio)

    return (
        {
            "x": region["x"],
            "y": region["y"],
            "w": left_width,
            "h": region["h"],
        },
        {
            "x": region["x"] + left_width,
            "y": region["y"],
            "w": region["w"] - left_width,
            "h": region["h"],
        },
    )
