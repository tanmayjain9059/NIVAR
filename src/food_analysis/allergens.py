"""
Allergen declaration extraction.
"""

import re


def parse_allergens(text):
    """
    Extract confirmed and possible allergens from an OCR block.

    Example:

        Contains Wheat, Milk & Soy.
        May Contains Tree Nuts, Peanut & Sesame.

    becomes:

        contains = ["Wheat", "Milk", "Soy"]
        may_contain = ["Tree Nuts", "Peanut", "Sesame"]
    """

    contains = []
    may_contain = []

    if not text:
        return contains, may_contain

    text = " ".join(
        text.split()
    )

    match = re.search(
        r"Contains\s+(.+?)(?=May Contains|$)",
        text,
        flags=re.IGNORECASE,
    )

    if match:

        value = match.group(1)

        value = value.replace(
            " & ",
            ", ",
        )

        contains = [
            item.strip().rstrip(".")
            for item in value.split(",")
            if item.strip()
        ]

    match = re.search(
        r"May Contains\s+(.+)$",
        text,
        flags=re.IGNORECASE,
    )

    if match:

        value = match.group(1)

        value = value.replace(
            " & ",
            ", ",
        )

        may_contain = [
            item.strip().rstrip(".")
            for item in value.split(",")
            if item.strip()
        ]

    return contains, may_contain
