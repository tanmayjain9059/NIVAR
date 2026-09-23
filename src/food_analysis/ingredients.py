"""Robust ingredient-section extraction from OCR text."""
import re

_START = re.compile(r"\b(?:ingredients?|composition)\b\s*[:\-]?\s*", re.I)
_END = re.compile(r"\b(?:nutrition(?:al)?\s+information|nutrition\s+facts|allergens?|contains|may\s+contain|manufactured\s+by|packed\s+by|marketed\s+by|consumer\s+care|customer\s+care|storage|store\s+in|directions|warning|best\s+before|use\s+by|expiry|mrp|net\s*(?:qty|quantity)|batch\s*(?:no|number))\b", re.I)
_GARBAGE = re.compile(r"\b(?:manufactured\s+by|packed\s+by|marketed\s+by|customer\s+care|consumer\s+care|store\s+in|best\s+before|use\s+by)\b", re.I)

def _norm(text): return re.sub(r"\s+", " ", str(text or "")).strip()

def _split_commas(text):
    out=[]; cur=[]; depth=0
    for ch in text:
        if ch=="(": depth+=1
        elif ch==")": depth=max(0,depth-1)
        if ch=="," and depth==0:
            item=_norm("".join(cur)).strip(" .;:-")
            if item: out.append(item)
            cur=[]
        else: cur.append(ch)
    item=_norm("".join(cur)).strip(" .;:-")
    if item: out.append(item)
    return out

def parse_ingredients(text):
    if not text: return []
    value=_norm(text)
    match=_START.search(value)
    if match: value=value[match.end():]
    stop=_END.search(value)
    if stop: value=value[:stop.start()]
    result=[]
    for item in _split_commas(value.strip(" :-.,;")):
        item=re.sub(r"\s+"," ",item).strip(" .;:-")
        if len(item)<2 or _GARBAGE.search(item) or re.fullmatch(r"[\d\s%./:-]+",item): continue
        result.append(item)
    return list(dict.fromkeys(result))
