"""
Conservative allergen declaration extraction.

The parser is intentionally line/section bounded so a declaration such
as "Contains Wheat & Sulphite" cannot consume an address or phone number
that follows it in noisy OCR.
"""

import re


_STOP_RE = re.compile(
    r"\b(?:manufactured|packed|marketed|imported|"
    r"customer\s+care|consumer\s+care|"
    r"address|phone|tel|toll[-\s]?free|www\.|"
    r"ingredients?|nutrition|nutritional|"
    r"mrp|net\s*(?:qty|quantity)|batch|"
    r"best\s+before|use\s+by|expiry)\b",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _items(value: str) -> list[str]:
    value = re.sub(r"\s*&\s*", ",", value)
    value = re.sub(r"\s+(?:and)\s+", ",", value, flags=re.IGNORECASE)
    value = re.sub(r"[.;]+\s*$", "", value)

    items = []
    for item in value.split(","):
        item = _normalize(item).strip(" .;:-")
        if len(item) >= 2 and not re.search(r"\d{3,}", item):
            items.append(item)
    return items


def _bounded_value(value: str) -> str:
    value = value.strip()
    stop = _STOP_RE.search(value)
    if stop:
        value = value[:stop.start()]
    return value.strip(" .;:-")


def parse_allergens(text):
    contains = []
    may_contain = []

    if not text:
        return contains, may_contain

    normalized = _normalize(text)

    # Process each declaration independently. This avoids one greedy
    # regex swallowing the rest of a noisy OCR block.
    for match in re.finditer(
        r"\b(?:may\s+contain|may\s+contains)\b\s*(.+?)(?="
        r"\b(?:contains|manufactured|packed|marketed|customer\s+care|"
        r"consumer\s+care|nutrition|ingredients?)\b|$)",
        normalized,
        flags=re.IGNORECASE,
    ):
        value = _bounded_value(match.group(1))
        may_contain.extend(_items(value))

    for match in re.finditer(
        r"\bcontains\b\s*(.+?)(?="
        r"\b(?:may\s+contain|may\s+contains|manufactured|packed|"
        r"marketed|customer\s+care|consumer\s+care|nutrition|"
        r"ingredients?)\b|$)",
        normalized,
        flags=re.IGNORECASE,
    ):
        value = _bounded_value(match.group(1))
        contains.extend(_items(value))

    # Preserve order while removing duplicates.
    contains = list(dict.fromkeys(contains))
    may_contain = list(dict.fromkeys(may_contain))

    return contains, may_contain
