"""
Legal Metrology compliance validation.
"""
from .rules import MANDATORY_DECLARATIONS, CONDITIONAL_DECLARATIONS, MANUAL_REVIEW_DECLARATIONS
from .enhanced_extractor import extract_declarations

DISCLAIMER=(
    "Automated OCR-based first-pass check. NOT DETECTED does not confirm "
    "absence on the physical package. Verify manually before making any compliance claim."
)
CORE_MANDATORY_KEYS=("manufacturer_packer_importer","net_quantity","manufacture_date","mrp","consumer_care")

def validate_declarations(raw_text,compliance_text=None,ocr_data=None):
    extracted=extract_declarations(raw_text,compliance_text,ocr_data=ocr_data)
    checks={}

    for key in CORE_MANDATORY_KEYS:
        rule=MANDATORY_DECLARATIONS.get(key,{"label":key.replace("_"," ").title()})
        result=extracted.get(key,{"detected":False,"matched_text":None})
        if result.get("value_missing"): status="REVIEW"
        elif result.get("detected"): status="FOUND"
        else: status="NOT_FOUND"
        checks[key]={
            "label":rule["label"],
            "detected":result.get("detected",False),
            "matched_text":result.get("matched_text"),
            "status":status,
        }
        if result.get("evidence"): checks[key]["evidence"]=result["evidence"]
        if result.get("value_missing"):
            checks[key]["note"]="Declaration label detected, but the required value was not detected. Manual verification required."

    for key,rule in MANDATORY_DECLARATIONS.items():
        if key in CORE_MANDATORY_KEYS: continue
        result=extracted.get(key,{"detected":False,"matched_text":None})
        if result.get("value_missing"): status="REVIEW"
        elif result.get("detected"): status="FOUND"
        else: status="NOT_FOUND"
        checks[key]={
            "label":rule["label"],
            "detected":result.get("detected",False),
            "matched_text":result.get("matched_text"),
            "status":status,
        }
        if result.get("evidence"): checks[key]["evidence"]=result["evidence"]
        if result.get("value_missing"):
            checks[key]["note"]="Declaration label detected, but the required value was not detected. Manual verification required."

    for key,rule in CONDITIONAL_DECLARATIONS.items():
        result=extracted.get(key,{"detected":False,"matched_text":None})
        checks[key]={
            "label":rule["label"],
            "detected":result.get("detected",False),
            "matched_text":result.get("matched_text"),
            "conditional":True,
            "status":"FOUND" if result.get("detected") else "REVIEW",
        }
        if result.get("evidence"): checks[key]["evidence"]=result["evidence"]

    for key,rule in MANUAL_REVIEW_DECLARATIONS.items():
        checks[key]={
            "label":rule["label"],
            "detected":None,
            "matched_text":None,
            "status":"REVIEW",
            "note":"Requires semantic extraction and manual verification.",
        }

    statuses=[checks[key]["status"] for key in CORE_MANDATORY_KEYS]
    found=statuses.count("FOUND"); review=statuses.count("REVIEW"); missing=statuses.count("NOT_FOUND")
    total=len(CORE_MANDATORY_KEYS)

    if missing: overall="NON_COMPLIANT"
    elif review: overall="REVIEW"
    elif found==total: overall="COMPLIANT"
    else: overall="REVIEW"

    return {
        "overall_status":overall,
        "checks":checks,
        "mandatory_declarations_detected":found,
        "mandatory_declarations_total":total,
        "mandatory_declarations_review":review,
        "mandatory_declarations_missing":missing,
        "disclaimer":DISCLAIMER,
    }
