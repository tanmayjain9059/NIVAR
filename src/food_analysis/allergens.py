"""Conservative, bounded allergen declaration extraction."""
import re

_STOP = re.compile(r"\b(?:manufactured|packed|marketed|imported|customer\s+care|consumer\s+care|address|phone|tel|toll[-\s]?free|www\.|ingredients?|nutrition|nutritional|mrp|net\s*(?:qty|quantity)|batch|best\s+before|use\s+by|expiry)\b", re.I)
_DECL = re.compile(r"\b(may\s+contain|may\s+contains|contains)\b\s*([^.!?\n]+)", re.I)

def _norm(x): return re.sub(r"\s+"," ",str(x or "")).strip()
def _items(value):
    value=re.sub(r"\s*&\s*",",",value)
    value=re.sub(r"\s+(?:and)\s+",",",value,flags=re.I)
    out=[]
    for item in value.split(","):
        item=_norm(item).strip(" .;:-")
        if 2<=len(item)<=60 and not re.search(r"\d{3,}",item): out.append(item)
    return out

def parse_allergens(text):
    contains=[]; may=[]
    if not text: return contains,may
    normalized=_norm(text)
    for match in _DECL.finditer(normalized):
        kind,value=match.group(1).lower(),match.group(2)
        stop=_STOP.search(value)
        if stop: value=value[:stop.start()]
        values=_items(value)
        if kind.startswith("may"): may.extend(values)
        else: contains.extend(values)
    return list(dict.fromkeys(contains)),list(dict.fromkeys(may))
