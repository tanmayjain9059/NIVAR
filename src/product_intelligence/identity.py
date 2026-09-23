"""
Product/brand identity extraction with semantic and layout safeguards.
"""

import re
from typing import Any

PRODUCT_LABEL_RE=re.compile(r"\b(?:product\s*name|name\s*of\s*product)\b\s*[:\-]?\s*(.+)",re.I)
BRAND_LABEL_RE=re.compile(r"\bbrand\b\s*[:\-]?\s*(.+)",re.I)
MANUFACTURER_BRAND_RE=re.compile(r"\b(?:manufactured|marketed|packed|imported)\s+by\b\s*[:\-]?\s*(.+)",re.I)
NOISE_RE=re.compile(r"\b(?:mrp|m\.r\.p|net\s*(?:qty|quantity|weight)|ingredients?|nutrition(?:al)?|energy|protein|carbohydrate|sugars?|fat|fiber|sodium|cholesterol|saturated|trans\s*fat|batch|lot|pkd|mfd|mfg|barcode|use\s*by|best\s*before|expiry|country\s+of\s+origin|contains|may\s+contain|keep\s+in|store\s+in|directions|warning|license|licence|fssai|customer\s+care|consumer\s+care|manufactured|packed|marketed|imported|www\.|@)\b",re.I)
NUTRITION_CONTEXT_RE=re.compile(r"\b(?:nutrition|nutritional|energy|protein|carbohydrate|sugar|fat|fiber|sodium|cholesterol|kcal|rda)\b",re.I)
INGREDIENT_HEADING_RE=re.compile(r"\b(?:ingredients?|composition)\b",re.I)

def _clean(value:Any)->str:return re.sub(r"\s+"," ",str(value or "").strip())
def _confidence(value:Any)->float:
    try:value=float(value)
    except (TypeError,ValueError):return 0.0
    if value>1:value/=100
    return max(0.0,min(value,1.0))
def _bbox(row):
    try:return {"x1":int(float(row["left"])),"y1":int(float(row["top"])),"x2":int(float(row["right"])),"y2":int(float(row["bottom"]))}
    except (KeyError,TypeError,ValueError):return None
def _evidence(row,text=None):
    box=_bbox(row)
    if box is None:return None
    return {"text":_clean(text if text is not None else row.get("text")),"confidence":_confidence(row.get("conf",0)),"bbox":box}

def _valid_candidate(text:str)->bool:
    text=_clean(text)
    if not 2<=len(text)<=100:return False
    if re.fullmatch(r"[\d\s./:%₹$€£+\-]+",text):return False
    if NOISE_RE.search(text):return False
    if sum(c.isalpha() for c in text)<2:return False
    if len(re.findall(r"\d",text))>max(3,len(text)//3):return False
    return True

def _clean_candidate(value:str)->str:
    value=_clean(value)
    value=re.split(r"\b(?:mrp|net\s*(?:qty|quantity)|ingredients?|nutrition|contains|may\s+contain|manufactured\s+by|marketed\s+by|packed\s+by|customer\s+care)\b",value,maxsplit=1,flags=re.I)[0]
    return value.strip(" :-.,;")

def _ingredient_terms(raw_text:str)->set[str]:
    text=_clean(raw_text); match=INGREDIENT_HEADING_RE.search(text)
    if not match:return set()
    tail=text[match.end():]
    stop=re.search(r"\b(?:nutrition(?:al)?|allergens?|contains|may\s+contain|manufactured\s+by|packed\s+by|consumer\s+care|customer\s+care|mrp|net\s*(?:qty|quantity)|best\s+before|expiry)\b",tail,re.I)
    if stop:tail=tail[:stop.start()]
    return {_clean(part).lower() for part in re.split(r"[,;\n]",tail) if 2<=len(_clean(part))<=80}

def _explicit_candidates(ocr_data):
    if ocr_data is None or getattr(ocr_data,"empty",True):return [],[]
    products=[];brands=[]
    for _,row in ocr_data.iterrows():
        text=_clean(row.get("text"))
        if not text:continue
        match=PRODUCT_LABEL_RE.search(text)
        if match:
            candidate=_clean_candidate(match.group(1))
            if _valid_candidate(candidate):
                ev=_evidence(row,text)
                if ev:products.append({"value":candidate,"confidence":ev["confidence"],"evidence":ev,"source":"explicit_product_label"})
        match=BRAND_LABEL_RE.search(text)
        if match:
            candidate=_clean_candidate(match.group(1))
            if _valid_candidate(candidate):
                ev=_evidence(row,text)
                if ev:brands.append({"value":candidate,"confidence":ev["confidence"],"evidence":ev,"source":"explicit_brand_label"})
        match=MANUFACTURER_BRAND_RE.search(text)
        if match:
            candidate=_clean_candidate(match.group(1))
            if _valid_candidate(candidate):
                ev=_evidence(row,text)
                if ev:brands.append({"value":candidate,"confidence":min(ev["confidence"],.90),"evidence":ev,"source":"manufacturer_label"})
    return products,brands

def _layout_candidates(ocr_data,raw_text):
    if ocr_data is None or getattr(ocr_data,"empty",True):return []
    try:
        image_width=max(float(ocr_data["right"].max()),1.0);image_height=max(float(ocr_data["bottom"].max()),1.0)
    except (KeyError,TypeError,ValueError):return []
    ingredient_terms=_ingredient_terms(raw_text);candidates=[]
    for _,row in ocr_data.iterrows():
        text=_clean(row.get("text"))
        if not _valid_candidate(text):continue
        try:left,top,right,bottom=map(float,(row["left"],row["top"],row["right"],row["bottom"]))
        except (KeyError,TypeError,ValueError):continue
        confidence=_confidence(row.get("conf",0));area_ratio=max(1.0,right-left)*max(1.0,bottom-top)/(image_width*image_height)
        score=confidence*55+min(area_ratio*12000,25)
        if top/image_height<.35:score+=14
        elif top/image_height<.50:score+=5
        words=len(text.split())
        if 2<=words<=8:score+=6
        if len(text)>=4:score+=4
        if NUTRITION_CONTEXT_RE.search(text):score-=35
        normalized=text.lower()
        if normalized in ingredient_terms:score-=55
        elif any(normalized==term or normalized in term or term in normalized for term in ingredient_terms):score-=35
        if words==1 and len(text)<=25:score-=8
        ev=_evidence(row)
        if ev:candidates.append({"value":text,"score":round(score,3),"confidence":confidence,"evidence":ev,"source":"layout_candidate"})
    return sorted(candidates,key=lambda item:item["score"],reverse=True)

def _candidate_is_generic_food_name(value: str) -> bool:
    """
    A product identity should describe the food itself, not the brand,
    manufacturer, address, marketing copy, or a nutrition/compliance field.
    """
    value = _clean(value)
    if not _valid_candidate(value):
        return False
    if _COMPANY_RE.search(value) or _ADDRESS_RE.search(value):
        return False
    if re.search(r"\b(?:manufactured|packed|marketed|imported)\s+by\b", value, re.I):
        return False
    if re.search(r"\b(?:brand|trademark|tm|®)\b", value, re.I):
        return False
    return True


_COMPANY_RE = re.compile(
    r"\b(?:pvt\.?\s*ltd\.?|private\s+limited|ltd\.?|limited|llp|"
    r"inc\.?|incorporated|corp\.?|corporation|co\.?|company|industries|"
    r"foods|food\s+products|enterprises|traders|manufacturers?)\b",
    re.I,
)
_ADDRESS_RE = re.compile(
    r"\b(?:plot|road|street|lane|avenue|industrial\s+area|estate|sector|"
    r"block|district|taluka|tehsil|village|nagar|colony|pin(?:code)?|postcode|"
    r"zip|near|opposite|opp\.?|phase|highway|city|state)\b",
    re.I,
)
_CATEGORY_RE = re.compile(
    r"\b(?:rice|basmati|flour|atta|maida|suji|sooji|dal|lentil|pulses?|"
    r"wheat|oats?|poha|flattened\s+rice|noodles?|pasta|biscuit(?:s)?|"
    r"cookies?|bread|rusk|namkeen|snack(?:s)?|chips?|mixture|cereal(?:s)?|"
    r"corn(?:flakes)?|muesli|chocolate|cocoa|tea|coffee|juice|drink|beverage|"
    r"milk|curd|yogurt|ghee|butter|cheese|oil|pickle|jam|sauce|ketchup|"
    r"spice(?:s)?|masala|salt|sugar|honey|jaggery|noodles?|vermicelli|"
    r"semolina|gram|chana|rajma|peas?|nuts?|almonds?|cashews?|"
    r"seasoning|powder|mix|blend|paste)\b",
    re.I,
)


def _product_label_candidates(raw_text: str, ocr_data):
    """
    Prefer explicit product-name/name-of-food declarations. These are the
    strongest signal because FSSAI requires the name of food to indicate the
    true nature of the food, and Legal Metrology requires the common/generic
    name of the commodity.
    """
    products = []
    if ocr_data is None or getattr(ocr_data, "empty", True):
        return products

    for _, row in ocr_data.iterrows():
        text = _clean(row.get("text"))
        if not text:
            continue

        match = PRODUCT_LABEL_RE.search(text)
        if not match:
            continue

        candidate = _clean_candidate(match.group(1))
        if not _candidate_is_generic_food_name(candidate):
            continue

        ev = _evidence(row, text)
        if ev:
            products.append({
                "value": candidate,
                "confidence": ev["confidence"],
                "score": ev["confidence"] * 100 + 35,
                "evidence": ev,
                "source": "explicit_product_label",
            })
    return products


def _front_panel_candidates(ocr_data, raw_text: str):
    """
    Find likely true-food names on the principal/front display area.

    Layout is only a fallback. It must have a plausible food/category term,
    enough OCR confidence, and must not resemble a brand/company/address or
    compliance/nutrition field.
    """
    if ocr_data is None or getattr(ocr_data, "empty", True):
        return []

    try:
        image_width = max(float(ocr_data["right"].max()), 1.0)
        image_height = max(float(ocr_data["bottom"].max()), 1.0)
    except (KeyError, TypeError, ValueError):
        return []

    ingredient_terms = _ingredient_terms(raw_text)
    candidates = []

    for _, row in ocr_data.iterrows():
        text = _clean(row.get("text"))
        if not _candidate_is_generic_food_name(text):
            continue

        try:
            left, top, right, bottom = map(
                float,
                (row["left"], row["top"], row["right"], row["bottom"]),
            )
        except (KeyError, TypeError, ValueError):
            continue

        confidence = _confidence(row.get("conf", 0))
        y_ratio = top / image_height
        area_ratio = (
            max(1.0, right - left) * max(1.0, bottom - top)
            / (image_width * image_height)
        )

        score = confidence * 55 + min(area_ratio * 12000, 20)

        # The FSSAI principal display panel is where the consumer first reads
        # the product identity, so upper/front-panel OCR gets a modest boost.
        if y_ratio < 0.35:
            score += 15
        elif y_ratio < 0.50:
            score += 7
        else:
            score -= 12

        words = len(text.split())
        if 2 <= words <= 8:
            score += 7
        if 4 <= len(text) <= 60:
            score += 4

        if _CATEGORY_RE.search(text):
            score += 25
        else:
            # Do not invent a product name from arbitrary decorative text.
            score -= 25

        if NUTRITION_CONTEXT_RE.search(text):
            score -= 60
        if text.lower() in ingredient_terms:
            score -= 60
        elif any(
            text.lower() == term
            or text.lower() in term
            or term in text.lower()
            for term in ingredient_terms
        ):
            score -= 40

        ev = _evidence(row)
        if ev:
            candidates.append({
                "value": text,
                "score": round(score, 3),
                "confidence": confidence,
                "evidence": ev,
                "source": "front_panel_semantic_candidate",
            })

    return sorted(candidates, key=lambda item: item["score"], reverse=True)


def _merge_adjacent_front_panel_candidates(ocr_data, candidates):
    """
    OCR often splits a food name into separate words/lines. Join nearby
    candidates when they are on the same visual line and preserve provenance.
    """
    if not candidates or ocr_data is None or getattr(ocr_data, "empty", True):
        return candidates

    rows = []
    for _, row in ocr_data.iterrows():
        text = _clean(row.get("text"))
        if not text:
            continue
        try:
            rows.append({
                "text": text,
                "left": float(row["left"]),
                "top": float(row["top"]),
                "right": float(row["right"]),
                "bottom": float(row["bottom"]),
                "conf": _confidence(row.get("conf", 0)),
                "row": row,
            })
        except (KeyError, TypeError, ValueError):
            continue

    if not rows:
        return candidates

    merged = list(candidates)
    for i, left in enumerate(rows):
        if not _candidate_is_generic_food_name(left["text"]):
            continue
        for right in rows[i + 1:]:
            if right["left"] < left["right"]:
                continue
            vertical_gap = abs(
                ((left["top"] + left["bottom"]) / 2)
                - ((right["top"] + right["bottom"]) / 2)
            )
            horizontal_gap = right["left"] - left["right"]
            line_height = max(left["bottom"] - left["top"], 1)
            if vertical_gap > line_height * 0.8 or horizontal_gap > line_height * 8:
                continue
            joined = _clean(f'{left["text"]} {right["text"]}')
            if not _candidate_is_generic_food_name(joined):
                continue
            if not _CATEGORY_RE.search(joined):
                continue
            evidence = _evidence(
                left["row"],
                joined,
            )
            if evidence:
                merged.append({
                    "value": joined,
                    "score": max(left["conf"], right["conf"]) * 100 + 45,
                    "confidence": min(left["conf"], right["conf"]),
                    "evidence": evidence,
                    "source": "front_panel_joined_candidate",
                })

    # Deduplicate by normalized value.
    dedup = {}
    for item in merged:
        key = item["value"].lower()
        if key not in dedup or item["score"] > dedup[key]["score"]:
            dedup[key] = item
    return sorted(dedup.values(), key=lambda item: item["score"], reverse=True)


def identify_product(raw_text: str, ocr_data=None) -> dict[str, Any]:
    explicit_products, explicit_brands = _explicit_candidates(ocr_data)

    # A product-name declaration is stronger than visual/layout inference.
    semantic_products = _product_label_candidates(raw_text, ocr_data)
    if semantic_products:
        selected_product = max(
            semantic_products,
            key=lambda item: (item["score"], item["confidence"]),
        )
    else:
        front_candidates = _front_panel_candidates(ocr_data, raw_text)
        front_candidates = _merge_adjacent_front_panel_candidates(
            ocr_data,
            front_candidates,
        )

        # Existing explicit candidates remain compatible, but only accept
        # them if they describe a plausible food and are not merely branding.
        fallback_explicit = [
            item for item in explicit_products
            if _candidate_is_generic_food_name(item["value"])
        ]

        all_candidates = front_candidates + fallback_explicit
        selected_product = None
        if all_candidates:
            best = max(
                all_candidates,
                key=lambda item: (item.get("score", item["confidence"] * 100), item["confidence"]),
            )
            # Conservative threshold: absence of a confident semantic product
            # name becomes REVIEW/null rather than a fabricated identity.
            if best.get("score", 0) >= 68:
                selected_product = best

    selected_brand = (
        max(explicit_brands, key=lambda item: item["confidence"])
        if explicit_brands
        else None
    )

    return {
        "product_name": selected_product["value"] if selected_product else None,
        "product_name_confidence": selected_product["confidence"] if selected_product else None,
        "product_name_evidence": selected_product["evidence"] if selected_product else None,
        "brand": selected_brand["value"] if selected_brand else None,
        "brand_confidence": selected_brand["confidence"] if selected_brand else None,
        "brand_evidence": selected_brand["evidence"] if selected_brand else None,
        "product_name_candidates": (
            semantic_products[:5]
            if semantic_products
            else (
                _merge_adjacent_front_panel_candidates(
                    ocr_data,
                    _front_panel_candidates(ocr_data, raw_text),
                )[:5]
                if ocr_data is not None
                else []
            )
        ),
        "brand_candidates": explicit_brands[:5],
    }
