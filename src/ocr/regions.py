"""
Region detection utilities for packaged-food labels.

This module is responsible only for locating logical sections
of a package label using OCR coordinates.

It does NOT perform OCR and does NOT parse the contents.
"""

from .engine import clean_word


def find_ingredients_heading(data):
    """
    Find the OCR bounding box corresponding to the
    INGREDIENTS heading.
    """

    for _, row in data.iterrows():

        word = clean_word(row["text"])

        if "ingredient" in word:
            return {
                "x": int(row["left"]),
                "y": int(row["top"]),
                "w": int(row["width"]),
                "h": int(row["height"]),
            }

    return None


def find_compliance_heading(data):
    """
    Find a likely heading for the compliance/declaration area.

    This is intentionally conservative because many packages
    do not have a single heading such as 'Declarations'.
    """

    keywords = [
        "manufacturedby",
        "manufactured",
        "marketedby",
        "packedby",
        "packed",
        "mrp",
        "batch",
        "consumer",
        "customer",
    ]

    for _, row in data.iterrows():

        word = clean_word(row["text"])

        for keyword in keywords:
            if keyword in word:
                return {
                    "x": int(row["left"]),
                    "y": int(row["top"]),
                    "w": int(row["width"]),
                    "h": int(row["height"]),
                }

    return None


def detect_nutrition_region(image, data, config):
    """
    Detect the nutrition information region.

    Current strategy:
    1. Locate a nutrition-related OCR heading.
    2. Build a region around it.
    3. Limit the region to avoid consuming the entire package.

    The exact heuristics remain configurable.
    """

    candidates = []

    nutrition_keywords = [
        "nutritional",
        "nutrition",
        "nutritionfacts",
        "nutritioninformation",
    ]

    for _, row in data.iterrows():

        word = clean_word(row["text"])

        if any(keyword in word for keyword in nutrition_keywords):

            candidates.append(
                {
                    "x": int(row["left"]),
                    "y": int(row["top"]),
                    "w": int(row["width"]),
                    "h": int(row["height"]),
                }
            )

    if not candidates:
        return None

    # Prefer the candidate appearing highest in the image.
    heading = sorted(
        candidates,
        key=lambda r: r["y"],
    )[0]

    x = max(
        0,
        heading["x"] - config.get("nutrition_left_padding", 500),
    )

    y = max(
        0,
        heading["y"] - config.get("nutrition_top_padding", 100),
    )

    right = min(
        image.shape[1],
        heading["x"]
        + heading["w"]
        + config.get("nutrition_right_padding", 1800),
    )

    bottom = min(
        image.shape[0],
        y + config.get("nutrition_height", 1800),
    )

    return {
        "x": x,
        "y": y,
        "w": right - x,
        "h": bottom - y,
    }


def detect_ingredients_region(
    image,
    data,
    nutrition_region,
    config,
):
    """
    Detect the ingredients section using the INGREDIENTS heading.

    If a nutrition region exists below the ingredients section,
    the ingredients region is stopped before it.
    """

    heading = find_ingredients_heading(data)

    if heading is None:
        return None

    x = max(
        0,
        heading["x"] - config.get("ingredients_left_padding", 200),
    )

    y = max(
        0,
        heading["y"] - config.get("ingredients_top_padding", 80),
    )

    right = min(
        image.shape[1],
        heading["x"]
        + heading["w"]
        + config.get("ingredients_right_padding", 1800),
    )

    default_bottom = min(
        image.shape[0],
        y + config.get("ingredients_height", 1000),
    )

    bottom = default_bottom

    # If nutrition starts below ingredients, stop before it.
    if nutrition_region is not None:

        nutrition_y = nutrition_region["y"]

        if nutrition_y > y:
            bottom = min(
                bottom,
                nutrition_y - config.get(
                    "section_gap",
                    30,
                ),
            )

    if bottom <= y:
        return None

    return {
        "x": x,
        "y": y,
        "w": right - x,
        "h": bottom - y,
    }


def detect_allergen_region(image, data, config):
    """
    Detect the allergen section.

    Searches for OCR words containing 'allergen'.
    """

    heading = None

    for _, row in data.iterrows():

        word = clean_word(row["text"])

        if "allergen" in word:

            heading = {
                "x": int(row["left"]),
                "y": int(row["top"]),
                "w": int(row["width"]),
                "h": int(row["height"]),
            }

            break

    if heading is None:
        return None

    x = max(
        0,
        heading["x"] - config.get(
            "allergen_left_padding",
            200,
        ),
    )

    y = max(
        0,
        heading["y"] - config.get(
            "allergen_top_padding",
            80,
        ),
    )

    right = min(
        image.shape[1],
        heading["x"]
        + heading["w"]
        + config.get(
            "allergen_right_padding",
            1800,
        ),
    )

    bottom = min(
        image.shape[0],
        y + config.get(
            "allergen_height",
            700,
        ),
    )

    return {
        "x": x,
        "y": y,
        "w": right - x,
        "h": bottom - y,
    }


def crop_region(image, region):
    """
    Crop an image using a region dictionary.

    Region format:
        {
            "x": ...,
            "y": ...,
            "w": ...,
            "h": ...
        }
    """

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
    """
    Detect the broad compliance/declaration area.

    Unlike nutrition and ingredients, compliance information
    is often distributed across multiple blocks, so this
    function returns a broad region rather than assuming a
    fixed table layout.
    """

    heading = find_compliance_heading(data)

    if heading is None:
        return None

    x = max(
        0,
        heading["x"] - config.get(
            "compliance_left_padding",
            500,
        ),
    )

    y = max(
        0,
        heading["y"] - config.get(
            "compliance_top_padding",
            100,
        ),
    )

    right = min(
        image.shape[1],
        heading["x"]
        + heading["w"]
        + config.get(
            "compliance_right_padding",
            1800,
        ),
    )

    bottom = min(
        image.shape[0],
        y + config.get(
            "compliance_height",
            2200,
        ),
    )

    return {
        "x": x,
        "y": y,
        "w": right - x,
        "h": bottom - y,
    }


def split_region_horizontally(region, ratio=0.5):
    """
    Split a region into left and right portions.

    Useful when compliance information is distributed
    across two columns.
    """

    if region is None:
        return None, None

    ratio = max(
        0.1,
        min(0.9, ratio),
    )

    x = region["x"]
    y = region["y"]
    w = region["w"]
    h = region["h"]

    left_width = int(w * ratio)

    left = {
        "x": x,
        "y": y,
        "w": left_width,
        "h": h,
    }

    right = {
        "x": x + left_width,
        "y": y,
        "w": w - left_width,
        "h": h,
    }

    return left, right
