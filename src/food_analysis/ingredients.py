"""Section-aware ingredient extraction.

The parser expects text from the ingredient section itself. It deliberately
does not use the entire package OCR as a fallback because doing so mixes
marketing copy, nutrition labels, and legal declarations into the ingredient
list.
"""

import re

_START = re.compile(
    r"\b(?:ingredients?|composition)\b\s*[:\-]?\s*",
    re.I,
)

_END = re.compile(
    r"\b(?:nutrition(?:al)?\s+information|nutrition\s+facts|allergens?|"
    r"contains|may\s+contain|manufactured\s+by|packed\s+by|marketed\s+by|"
    r"imported\s+by|consumer\s+care|customer\s+care|storage|store\s+in|"
    r"directions|warning|best\s+before|use\s+by|expiry|mrp|"
    r"net\s*(?:qty|quantity)|batch\s*(?:no|number))\b",
    re.I,
)

_NOISE = re.compile(
    r"^(?:from the first|it's heaven|the clinking|everyone's|for these moments|"
    r"discover our full range|cookie heaven)\b",
    re.I,
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _split_commas(text: str) -> list[str]:
    out = []
    current = []
    depth = 0

    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)

        if char == "," and depth == 0:
            item = _norm("".join(current)).strip(" .;:-")
            if item:
                out.append(item)
            current = []
        else:
            current.append(char)

    item = _norm("".join(current)).strip(" .;:-")
    if item:
        out.append(item)

    return out


def parse_ingredients(text: str) -> list[str]:
    text = _norm(text)
    if not text:
        return []

    start = _START.search(text)
    if start:
        text = text[start.end():]

    end = _END.search(text)
    if end:
        text = text[:end.start()]

    result = []

    for item in _split_commas(text):
        item = _norm(item).strip(" .;:-")

        if len(item) < 2 or len(item) > 180:
            continue

        if _NOISE.search(item):
            continue

        if re.fullmatch(r"[\d\s%./:+\-]+", item):
            continue

        if sum(char.isalpha() for char in item) < 2:
            continue

        if len(item.split()) > 28:
            continue

        result.append(item)

    unique = []
    seen = set()

    for item in result:
        key = re.sub(r"\s+", " ", item).lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique
