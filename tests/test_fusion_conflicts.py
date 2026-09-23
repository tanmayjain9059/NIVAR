from src.product_intelligence.fusion import fuse_image_analyses

CORE=("manufacturer_packer_importer","net_quantity","manufacture_date","mrp","consumer_care")

def compliance(values):
    checks={}
    for key in CORE:
        value=values.get(key)
        checks[key]={"status":"FOUND" if value else "NOT_FOUND","evidence":{"value":value,"confidence":0.95} if value else {}}
    return {"overall_status":"COMPLIANT","checks":checks}


def image(i,name,product="7 Grain Biscuit",values=None):
    return {"_image_id":i,"_filename":name,"product_identity":{"product_name":product,"product_name_confidence":.95,"product_name_evidence":{"text":product}},"legal_metrology_compliance":compliance(values or {})}


def test_found_value_on_any_image_is_fused():
    a={"mrp":"₹50","manufacturer_packer_importer":"Patanjali","net_quantity":"100 g","manufacture_date":"08/2026","consumer_care":"1800"}
    b={"manufacturer_packer_importer":"Patanjali","net_quantity":"100 g","manufacture_date":"08/2026","consumer_care":"1800"}
    result=fuse_image_analyses([image("front","front.jpg",values=a),image("back","back.jpg",values=b)])
    assert result["legal_metrology_compliance"]["checks"]["mrp"]["status"]=="FOUND"


def test_conflicting_found_values_force_review():
    base={"manufacturer_packer_importer":"Patanjali","net_quantity":"100 g","manufacture_date":"08/2026","consumer_care":"1800"}
    a={**base,"mrp":"₹50"}; b={**base,"mrp":"₹55"}
    result=fuse_image_analyses([image("front","front.jpg",values=a),image("side","side.jpg",values=b)])
    check=result["legal_metrology_compliance"]["checks"]["mrp"]
    assert check["status"]=="REVIEW"
    assert check["conflict"] is True
    assert result["legal_metrology_compliance"]["overall_status"]=="REVIEW"
