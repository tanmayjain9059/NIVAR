"""
Robust ingredient-section extraction from OCR text.
"""

import re


_SECTION_START_RE = re.compile(
    r"\b(?:ingredients?|composition)\s*[:\-]?\s*",
    re.IGNORECASE,
)

_SECTION_END_RE = re.compile(
    r"\b(?:nutrition(?:al)?\s+information|nutrition\s+facts|"
    r"allergens?|contains|may\s+contain|"
    r"manufactured\s+by|packed\s+by|marketed\s+by|"
    r"consumer\s+care|customer\s+care|"
    r"storage|store\s+in|directions|warning|"
    r"best\s+before|use\s+by|expiry|"
    r"mrp|net\s*(?:qty|quantity)|batch\s*(?:no|number))\b",
    re.IGNORECASE,
)

_GARBAGE_RE = re.compile(
    r"\b(?:made\s+from|chocolate\s+indulgence|"
    r"manufactured\s+by|packed\s+by|marketed\s+by|"
    r"customer\s+care|consumer\s+care|"
    r"store\s+in|best\s+before|use\s+by)\b",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _split_commas(text: str) -> list[str]:
    result = []
    current = []
    depth = 0

    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)

        if char == "," and depth == 0:
            value = _normalize("".join(current)).strip(" .;:-")
            if value:
                result.append(value)
            current = []
        else:
            current.append(char)

    value = _normalize("".join(current)).strip(" .;:-")
    if value:
        result.append(value)

    return result


def parse_ingredients(text):
    if not text:
        return []

    normalized = _normalize(text)
    match = _SECTION_START_RE.search(normalized)

    if match:
        normalized = normalized[match.end():]

    stop = _SECTION_END_RE.search(normalized)
    if stop:
        normalized = normalized[:stop.start()]

    normalized = normalized.strip(" :-.,;")
    if not normalized:
        return []

    values = []
    for item in _split_commas(normalized):
        item = re.sub(r"\s+", " ", item).strip(" .;:-")
        if len(item) < 2:
            continue
        if _GARBAGE_RE.search(item):
            continue
        if re.fullmatch(r"[\d\s%./:-]+", item):
            continue
        values.append(item)

    return values
