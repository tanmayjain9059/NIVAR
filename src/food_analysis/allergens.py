"""Conservative allergen declaration extraction."""

import re

_DECL = re.compile(
    r"\b(may\s+contain(?:s)?|contains)\b\s*([^.!?\n]+)",
    re.I,
)

_STOP = re.compile(
    r"\b(?:manufactured|packed|marketed|imported|customer\s+care|"
    r"consumer\s+care|address|phone|tel|toll[-\s]?free|www\.|ingredients?|"
    r"nutrition|nutritional|mrp|net\s*(?:qty|quantity)|batch|best\s+before|"
    r"use\s+by|expiry)\b",
    re.I,
)

_ALLOWED = {
    "wheat": "Wheat",
    "milk": "Milk",
    "soy": "Soy",
    "soya": "Soy",
    "peanut": "Peanut",
    "groundnut": "Peanut",
    "sesame": "Sesame",
    "mustard": "Mustard",
    "tree nuts": "Tree Nuts",
    "tree nut": "Tree Nuts",
    "nuts": "Tree Nuts",
    "nut": "Tree Nuts",
    "almond": "Tree Nuts",
    "almonds": "Tree Nuts",
    "cashew": "Tree Nuts",
    "cashews": "Tree Nuts",
}

_CANONICAL_PATTERNS = sorted(
    _ALLOWED.items(),
    key=lambda item: len(item[0]),
    reverse=True,
)


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _extract_known_allergens(value: str) -> list[str]:
    value = _norm(value).lower()
    matches = []

    for alias, canonical in _CANONICAL_PATTERNS:
        for match in re.finditer(rf"\b{re.escape(alias)}\b", value):
            matches.append((match.start(), canonical))

    found = []
    for _, canonical in sorted(matches, key=lambda item: item[0]):
        if canonical not in found:
            found.append(canonical)

    return found


def parse_allergens(text: str) -> tuple[list[str], list[str]]:
    normalized = _norm(text)

    if not normalized:
        return [], []

    contains = []
    may_contain = []

    for match in _DECL.finditer(normalized):
        kind = match.group(1).lower()
        value = match.group(2)

        stop = _STOP.search(value)
        if stop:
            value = value[:stop.start()]

        values = _extract_known_allergens(value)

        if kind.startswith("may"):
            may_contain.extend(values)
        else:
            contains.extend(values)

    return list(dict.fromkeys(contains)), list(dict.fromkeys(may_contain))
