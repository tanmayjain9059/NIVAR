"""
Evidence-oriented Legal Metrology declaration extraction.

This layer supplements the existing extractor with multiline and multilingual
label matching. It remains conservative: a declaration is FOUND only when
there is useful value/contact evidence, otherwise REVIEW is returned.
"""

import re
from typing import Any

from .evidence import grouped_text, nearby_candidates

LABELS = {
    "manufacturer_packer_importer": [
        r"manufactured\s+by", r"packed\s+by", r"marketed\s+by", r"imported\s+by",
        r"निर्माता", r"निर्मित\s*द्वारा", r"पैक\s*(?:द्वारा|किया)",
        r"తయారీదారు", r"తయారు\s*చేసిన", r"ప్యాక్",
        r"உற்பத்தியாளர்", r"தயாரித்தவர்", r"பேக்",
        r"ತಯಾರಕರು", r"ತಯಾರಿಸಿದ", r"പാക്ക്", r"നിർമ്മാതാവ്",
        r"প্রস্তুতকারক", r"উৎপাদিত", r"ઉત્પાદક", r"ਨਿਰਮਾਤਾ", r"ନିର୍ମାତା",
    ],
    "net_quantity": [
        r"net\s*(?:weight|quantity|qty|wt|wgt)", r"n\.?\s*qty",
        r"नेट\s*(?:मात्रा|वजन)", r"शुद्ध\s*(?:मात्रा|वजन)",
        r"నికర\s*(?:పరిమాణం|బరువు)", r"நிகர\s*(?:அளவு|எடை)",
        r"ನಿವ್ವಳ\s*(?:ಪ್ರಮಾಣ|ತೂಕ)", r"ശുദ്ധ\s*(?:അളവ്|ഭാരം)",
        r"নেট\s*(?:পরিমাণ|ওজন)", r"ચોખ્ખી\s*(?:માત્રા|વજન)",
        r"ਸ਼ੁੱਧ\s*(?:ਮਾਤਰਾ|ਭਾਰ)", r"ନେଟ\s*(?:ପରିମାଣ|ଓଜନ)",
    ],
    "manufacture_date": [
        r"\bmfd\b", r"\bmfg(?:\.?\s*date)?\b",
        r"manufacture(?:d)?\s+date", r"date\s+of\s+(?:manufacture|packaging)",
        r"\bpkd\b", r"packed\s+on",
        r"निर्माण\s*(?:तिथि|दिनांक)", r"पैकिंग\s*(?:तिथि|दिनांक)",
        r"निर्मित\s*(?:तिथि|दिनांक)", r"తయారీ\s*(?:తేదీ|తేది)", r"ప్యాకింగ్\s*(?:తేదీ|తేది)",
        r"உற்பத்தி\s*(?:தேதி|நாள்)", r"பேக்கிங்\s*(?:தேதி|நாள்)",
        r"ತಯಾರಿಕೆ\s*(?:ದಿನಾಂಕ|ದಿನ)", r"പാക്കിംഗ്\s*(?:തീയതി|ദിവസം)",
        r"উৎপাদন\s*(?:তারিখ|দিন)", r"પેકિંગ\s*(?:તારીખ|તારીખ)",
        r"ਨਿਰਮਾਣ\s*(?:ਮਿਤੀ|ਤਾਰੀਖ)", r"ପ୍ୟାକିଂ\s*(?:ତାରିଖ|ଦିନ)",
    ],
    "mrp": [
        r"m\s*\.?\s*r\s*\.?\s*p\s*\.?", r"maximum\s+retail\s+price",
        r"retail\s+sale\s+price", r"अधिकतम\s*खुदरा\s*मूल्य", r"अधिकतम\s*विक्रय\s*मूल्य",
        r"గరిష్ట\s*చిల్లర\s*ధర", r"அதிகபட்ச\s*சில்லறை\s*விலை",
        r"ಗರಿಷ್ಠ\s*ಚಿಲ್ಲರೆ\s*ಬೆಲೆ", r"പരമാവധി\s*ചില്ലറ\s*വില",
        r"সর্বোচ্চ\s*খুচরা\s*মূল্য", r"મહત્તમ\s*છૂટક\s*કિંમત",
        r"ਅਧਿਕਤਮ\s*ਖੁਦਰਾ\s*ਕੀਮਤ", r"ସର୍ବାଧିକ\s*ଖୁଚୁରା\s*ମୂଲ୍ୟ",
    ],
    "consumer_care": [
        r"consumer\s+care", r"customer\s+care", r"consumer\s+complaints?",
        r"customer\s+service", r"helpline", r"toll[-\s]?free", r"contact\s+us", r"write\s+to",
        r"उपभोक्ता\s*(?:सेवा|देखभाल)", r"ग्राहक\s*(?:सेवा|देखभाल)", r"हेल्पलाइन",
        r"వినియోగదారుల\s*(?:సేవ|సంరక్షణ)", r"కస్టమర్\s*కేర్", r"హెల్ప్‌లైన్",
        r"வாடிக்கையாளர்\s*(?:சேவை|பராமரிப்பு)", r"வாடிக்கையாளர்\s*பராமரிப்பு",
        r"ಗ್ರಾಹಕ\s*(?:ಸೇವೆ|ಪಾಲನೆ)", r"ഉപഭോക്തൃ\s*(?:സേവനം|പരിചരണം)",
        r"গ্রাহক\s*(?:পরিষেবা|সেবা)", r"ગ્રાહક\s*(?:સેવા|સંભાળ)",
        r"ਗਾਹਕ\s*(?:ਸੇਵਾ|ਦੇਖਭਾਲ)", r"ଗ୍ରାହକ\s*(?:ସେବା|ଯତ୍ନ)",
    ],
}

UNITS=r"(?:g|gm|gms|kg|mg|ml|l|ltr|litre|liter|pcs|pieces|pc|units?|किग्रा|ग्राम|मि?ली)"
QUANTITY_RE=re.compile(rf"\b\d+(?:\.\d+)?\s*{UNITS}\b",re.I)
DATE_RE=re.compile(r"(?<!\d)(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}[./-]\d{2,4}|\d{1,2}\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[ ./-]?\d{2,4}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[ ./-]\d{2,4}|\d{1,2}(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\d{2,4})(?!\d)",re.I)
MRP_RE=re.compile(r"(?:₹|rs\.?|inr)?\s*\d{1,5}(?:\.\d{1,2})?",re.I)
EMAIL_RE=re.compile(r"\b[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}\b",re.I)
PHONE_RE=re.compile(r"(?<!\d)(?:(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}|(?:0\d{2,5}[\s-]?\d{5,8})|(?:1800|1860)[\s-]?\d{2,4}[\s-]?\d{3,4})(?!\d)")

def _norm(text): return re.sub(r"\s+"," ",str(text or "").strip())
def _conf(v):
    try:
        v=float(v)
        return v/100 if v>1 else max(0.0,min(v,1.0))
    except (TypeError,ValueError): return 0.0

def _evidence(row,text=None):
    try:
        return {"text":_norm(text if text is not None else row.get("text")),
                "confidence":_conf(row.get("conf",0)),
                "bbox":{"x1":int(row["left"]),"y1":int(row["top"]),
                        "x2":int(row["right"]),"y2":int(row["bottom"])}}
    except (KeyError,TypeError,ValueError): return None

def _ocr_text(ocr_data):
    """Build logical OCR lines by merging boxes on the same visual baseline."""
    return grouped_text(ocr_data)


def _rows(ocr_data):
    if ocr_data is None or getattr(ocr_data,"empty",True): return []
    rows=[]
    for _,row in ocr_data.iterrows():
        text=_norm(row.get("text"))
        if text: rows.append(row)
    return rows

def _search_text(raw_text, ocr_data):
    parts = [str(raw_text or "").strip(), _ocr_text(ocr_data)]
    return "\n".join(part for part in parts if part)


def _label_match(text,patterns):
    return next((re.search(p,text,re.I) for p in patterns if re.search(p,text,re.I)),None)

def _nearby_values(label_row,ocr_data,predicate,max_gap=1500):
    try:
        label_group={
            "left":float(label_row["left"]),
            "top":float(label_row["top"]),
            "right":float(label_row["right"]),
            "bottom":float(label_row["bottom"]),
        }
    except (KeyError,TypeError,ValueError):
        return []
    return nearby_candidates(label_group,ocr_data,predicate)

def _result(detected,matched_text,evidence=None,value_missing=False):
    result={"detected":detected,"matched_text":matched_text}
    if evidence: result["evidence"]=evidence
    if value_missing: result["value_missing"]=True
    return result


_COMPANY_SUFFIX_RE=re.compile(
    r"\b(?:pvt\.?\s*ltd\.?|private\s+limited|ltd\.?|limited|llp|inc\.?|incorporated|corp\.?|corporation|co\.?|company|industries|foods|food\s+products|enterprises|traders|manufacturers?)\b",
    re.I,
)
def _entity_fragment(value):
    """Keep the company/entity portion when OCR puts the address on the same line."""
    value=_norm(value).strip(" :-.,;")
    company=_COMPANY_SUFFIX_RE.search(value)
    if company:
        suffix_end=company.end()
        comma=value.find(",",suffix_end)
        if 0 <= comma-suffix_end <= 80:
            return value[:suffix_end].strip(" :-.,;")
    return value


_ADDRESS_RE=re.compile(
    r"\b(?:road|rd\.?|street|st\.?|lane|ln\.?|avenue|ave\.?|industrial\s+area|estate|plot|floor|building|bldg|sector|block|district|dist\.?|taluka|tehsil|village|nagar|colony|pin(?:code)?|postcode|zip|near|opp\.?|opposite|phase|highway|city|state|scheme|survey|no\.?)\b",
    re.I,
)

def _manufacturer_candidates(text,ocr,label_row=None):
    candidates=[]
    if label_row is not None:
        for score,row in _nearby_values(
            label_row,
            ocr,
            lambda x: bool(re.search(r"[A-Za-z\u0900-\u0DFF]{3,}",x))
            and not _label_match(x,LABELS["manufacturer_packer_importer"]),
            1000,
        ):
            candidates.append((_norm(row.get("text")),score,_evidence(row)))
    pattern=_label_match(text,LABELS["manufacturer_packer_importer"])
    if pattern:
        tail=text[pattern.end():]
        stop_patterns=[]
        for key,patterns in LABELS.items():
            if key=="manufacturer_packer_importer":
                continue
            stop_patterns.extend(patterns)
        stops=[re.search(pat,tail,re.I) for pat in stop_patterns]
        stops=[m.start() for m in stops if m]
        if stops:
            tail=tail[:min(stops)]
        other_labels=[]
        for key,patterns in LABELS.items():
            if key!="manufacturer_packer_importer":
                other_labels.extend(patterns)
        for line in re.split(r"\n+",tail)[:5]:
            value=_norm(line).strip(" :-.,;")
            if not value:
                continue
            if any(re.search(pattern,value,re.I) for pattern in other_labels):
                break
            candidates.append((value,60,None))
    return candidates

def _manufacturer_value(candidates):
    ranked=[]
    seen=set()
    for value,base_score,evidence in candidates:
        value=_entity_fragment(value)
        if len(value)<3:
            continue
        key=value.lower()
        if key in seen:
            continue
        seen.add(key)
        score=float(base_score)
        if _COMPANY_SUFFIX_RE.search(value):
            score+=90
        if _ADDRESS_RE.search(value):
            score-=70
        if re.search(r"\b(?:phone|tel|mob|mobile|email|www\.|http)\b|@",value,re.I):
            score-=100
        if re.search(r"\b\d{6}\b",value):
            score-=50
        if len(value)>120:
            score-=30
        if re.search(r"[A-Za-z]{3,}\s+(?:pvt|private|ltd|limited|llp|inc|corp|company|industries|foods?)",value,re.I):
            score+=45
        ranked.append((score,value,evidence))
    return max(ranked,key=lambda x:x[0]) if ranked else None

def _manufacturer(text,ocr):
    pattern=_label_match(text,LABELS["manufacturer_packer_importer"])
    labels=_rows(ocr)
    label_rows=[
        row for row in labels
        if _label_match(_norm(row.get("text")),LABELS["manufacturer_packer_importer"])
    ]

    candidates=[]
    for row in label_rows:
        candidates.extend(_manufacturer_candidates(text,ocr,row))
    if pattern:
        candidates.extend(_manufacturer_candidates(text,ocr,None))

    chosen=_manufacturer_value(candidates)
    if chosen:
        score,value,evidence=chosen
        label_text=_norm(pattern.group(0) if pattern else (
            label_rows[0].get("text") if label_rows else "Manufacturer/Packer/Importer"
        ))

        # Legal Metrology requires the manufacturer's/packer's/importer's
        # name AND address. Keep the UI value focused on the entity name,
        # but retain address evidence separately and require it for FOUND.
        address_candidates=[]
        for line in re.split(r"\n+", text):
            line=_norm(line)
            if not line or line.lower()==value.lower():
                continue
            if _ADDRESS_RE.search(line) and not _label_match(line,LABELS["manufacturer_packer_importer"]):
                address_candidates.append(line)
        address=address_candidates[0] if address_candidates else None

        result=_result(
            True,
            f"{label_text} {value}",
            evidence,
            value_missing=not bool(address),
        )
        result["manufacturer_name"]=value
        result["address_detected"]=bool(address)
        if address:
            result["address_text"]=address
        return result

    if pattern:
        return _result(True,pattern.group(0),None,True)
    return _result(False,None)

def _net_quantity(text,ocr):
    pattern=_label_match(text,LABELS["net_quantity"])
    if pattern:
        tail=text[pattern.end():pattern.end()+120]
        m=QUANTITY_RE.search(tail)
        if m:return _result(True,m.group(0))
    for row in _rows(ocr):
        if _label_match(_norm(row.get("text")),LABELS["net_quantity"]):
            near=_nearby_values(row,ocr,lambda x:bool(QUANTITY_RE.search(x)),1500)
            if near:return _result(True,f"{row.get('text')} {near[0][1].get('text')}",_evidence(near[0][1]))
    return _result(bool(pattern),pattern.group(0) if pattern else None,None, bool(pattern))

def _manufacture_date(text,ocr):
    for row in _rows(ocr):
        label=_norm(row.get("text"))
        if _label_match(label,LABELS["manufacture_date"]) and not re.search(r"best\s*before|expiry|use\s*by",label,re.I):
            near=_nearby_values(row,ocr,lambda x:bool(DATE_RE.search(x)),1500)
            if near:
                value_row=near[0][1]
                return _result(True,f"{label} {value_row.get('text')}",_evidence(value_row))
    pattern=_label_match(text,LABELS["manufacture_date"])
    if pattern:
        tail=text[pattern.end():pattern.end()+180]
        m=DATE_RE.search(tail)
        if m:return _result(True,m.group(0))
    return _result(bool(pattern),pattern.group(0) if pattern else None,None,bool(pattern))

def _mrp(text,ocr):
    for line in str(text or "").splitlines():
        label=_label_match(line,LABELS["mrp"])
        if label:
            tail=line[label.end():]
            m=MRP_RE.search(tail)
            if m:return _result(True,f"{label.group(0)} {m.group(0).strip()}")
    for row in _rows(ocr):
        label=_norm(row.get("text"))
        if _label_match(label,LABELS["mrp"]):
            near=_nearby_values(row,ocr,lambda x:bool(re.fullmatch(r"(?:₹|rs\.?|inr)?\s*\d{1,5}(?:\.\d{1,2})?",x,re.I)),1500)
            if near:return _result(True,f"{label} {near[0][1].get('text')}",_evidence(near[0][1]))
    pattern=_label_match(text,LABELS["mrp"])
    return _result(bool(pattern),pattern.group(0) if pattern else None,None,bool(pattern))

def _consumer(text,ocr):
    pattern=_label_match(text,LABELS["consumer_care"])
    if pattern:
        tail=text[pattern.end():pattern.end()+400]
        contact=EMAIL_RE.search(tail) or PHONE_RE.search(tail)
        if contact:return _result(True,f"{pattern.group(0)} {contact.group(0)}")
    for row in _rows(ocr):
        label=_norm(row.get("text"))
        if _label_match(label,LABELS["consumer_care"]):
            near=_nearby_values(row,ocr,lambda x:bool(EMAIL_RE.search(x) or PHONE_RE.search(x)),1500)
            if near:return _result(True,f"{label} {near[0][1].get('text')}",_evidence(near[0][1]))
    return _result(bool(pattern),pattern.group(0) if pattern else None,None,bool(pattern))

def extract_declarations(raw_text,compliance_text=None,ocr_data=None):
    text=_search_text(f"{compliance_text or ''}\n{raw_text or ''}", ocr_data)
    return {
        "manufacturer_packer_importer":_manufacturer(text,ocr_data),
        "net_quantity":_net_quantity(text,ocr_data),
        "manufacture_date":_manufacture_date(text,ocr_data),
        "mrp":_mrp(text,ocr_data),
        "consumer_care":_consumer(text,ocr_data),
        "country_of_origin":_result(
            bool(re.search(r"country\s+of\s+origin|made\s+in",text,re.I)),
            (re.search(r"country\s+of\s+origin|made\s+in",text,re.I).group(0)
             if re.search(r"country\s+of\s+origin|made\s+in",text,re.I) else None)
        ),
    }
