"""
Food label analysis package.
"""

from .nutrition import NUTRIENTS, parse_nutrition_table
from .ingredients import parse_ingredients
from .allergens import parse_allergens

__all__ = [
    "NUTRIENTS",
    "parse_nutrition_table",
    "parse_ingredients",
    "parse_allergens",
]
