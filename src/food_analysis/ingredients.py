"""
Ingredient extraction and cleanup.
"""

import re


def parse_ingredients(text):
    """
    Convert an OCR ingredient block into a list of ingredients.

    Commas inside parentheses are preserved so compound
    ingredients such as vegetable-oil blends remain intact.
    """

    if not text:
        return []

    text = re.sub(
        r"^\s*INGREDIENTS?\s*:?",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = " ".join(
        text.split()
    )

    stop_phrases = [
        "Nutritional Information",
        "Nutrition Information",
        "Allergen:",
        "Allergens:",
    ]

    for phrase in stop_phrases:

        index = text.lower().find(
            phrase.lower()
        )

        if index != -1:
            text = text[:index]

    ingredients = []

    current = ""
    parentheses = 0

    for char in text:

        if char == "(":
            parentheses += 1

        elif char == ")":
            parentheses = max(
                0,
                parentheses - 1,
            )

        if (
            char == ","
            and parentheses == 0
        ):

            if current.strip():
                ingredients.append(
                    current.strip()
                )

            current = ""

        else:
            current += char

    if current.strip():
        ingredients.append(
            current.strip()
        )

    garbage_phrases = [
        "made from",
        "chocolate indulgence",
        "store in",
        "manufactured by",
    ]

    cleaned = []

    for ingredient in ingredients:

        ingredient = (
            ingredient
            .strip()
            .rstrip(".,;")
        )

        if len(ingredient) < 2:
            continue

        if any(
            phrase in ingredient.lower()
            for phrase in garbage_phrases
        ):
            continue

        cleaned.append(ingredient)

    return cleaned
