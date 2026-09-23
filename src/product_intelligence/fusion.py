"""Cross-image evidence fusion for one packaged product."""
from collections import defaultdict
from copy import deepcopy
from typing import Any

CORE_KEYS=("manufacturer_packer_importer","net_quantity","manufacture_date","mrp","consumer_care")

def _norm(v): return " ".join(str(v or "").strip().lower().split())
def _conf(v):
    try: v=float(v)
    except (TypeError,ValueError): return 0.0
    return v/100 if v>1 else max(0.0,min(v,1.0))

def _choose(candidates):
    valid=[c for c in candidates if c.get("value")]
    if not valid: return {"value":None,"confidence":None,"evidence":None,"support_count":0,"conflict":False}
    groups=defaultdict(list)
    for c in valid: groups[_norm(c["value"])].append(c)
    ranked=[]
    for key,group in groups.items():
        strongest=max(group,key=lambda x:_conf(x.get("confidence")))
        avg=sum(_conf(x.get("confidence")) for x in group)/len(group)
        ranked.append({"value":strongest["value"],"confidence":min(1,avg+min(.1,(len(group)-1)*.025)),"evidence":strongest.get("evidence"),"support_count":len(group),"normalized":key})
    ranked.sort(key=lambda x:(x["support_count"],x["confidence"]),reverse=True)
    winner=ranked[0]
    winner["conflict"]=len(ranked)>1
    if winner["conflict"]: winner["alternatives"]=ranked[1:4]
    return winner

def _merge_checks(results):
    keys=set()
    for result in results:
        keys.update(result.get("legal_metrology_compliance",{}).get("checks",{}).keys())
    merged={}
    for key in sorted(keys):
        candidates=[]
        for result in results:
            check=result.get("legal_metrology_compliance",{}).get("checks",{}).get(key)
            if check:
                item=deepcopy(check); item["_image_id"]=result.get("_image_id"); candidates.append(item)
        if not candidates: continue
        found=[x for x in candidates if x.get("status")=="FOUND"]
        review=[x for x in candidates if x.get("status")=="REVIEW"]
        missing=[x for x in candidates if x.get("status")=="NOT_FOUND"]
        pool=found or review or missing
        selected=max(pool,key=lambda x:_conf((x.get("evidence") or {}).get("confidence"))) if found else pool[0]
        merged[key]=deepcopy(selected)
        merged[key]["source_images"]=[x["_image_id"] for x in pool]
        merged[key]["support_count"]=len(pool)
        # Preserve disagreement instead of silently hiding it.
        values={_norm((x.get("evidence") or {}).get("value") or x.get("value")) for x in found if (x.get("evidence") or {}).get("value") or x.get("value")}
        if len(values)>1:
            merged[key]["conflict"]=True
            merged[key]["status"]="REVIEW"
            merged[key]["conflict_reason"]="Different FOUND values were detected across images."
            merged[key]["conflicting_evidence"]=[{k:v for k,v in x.items() if not k.startswith("_")} for x in found]
    return merged

def _overall(compliance):
    result=deepcopy(compliance); checks=result.get("checks",{})
    statuses=[checks[k].get("status") for k in CORE_KEYS if k in checks]
    missing=statuses.count("NOT_FOUND"); review=statuses.count("REVIEW"); found=statuses.count("FOUND")
    result["overall_status"]="NON_COMPLIANT" if missing else ("REVIEW" if review or found<len(CORE_KEYS) else "COMPLIANT")
    result["mandatory_declarations_detected"]=found
    result["mandatory_declarations_total"]=len(CORE_KEYS)
    result["mandatory_declarations_review"]=review
    result["mandatory_declarations_missing"]=missing
    return result

def fuse_image_analyses(image_results:list[dict[str,Any]])->dict[str,Any]:
    if not image_results: raise ValueError("At least one image analysis is required.")
    products=[]; brands=[]
    for result in image_results:
        identity=result.get("product_identity",{}); image_id=result.get("_image_id")
        if identity.get("product_name"): products.append({"value":identity["product_name"],"confidence":identity.get("product_name_confidence"),"evidence":{**(identity.get("product_name_evidence") or {}),"image_id":image_id}})
        if identity.get("brand"): brands.append({"value":identity["brand"],"confidence":identity.get("brand_confidence"),"evidence":{**(identity.get("brand_evidence") or {}),"image_id":image_id}})
    pi=_choose(products); bi=_choose(brands)
    compliance_sources=[r.get("legal_metrology_compliance") for r in image_results if r.get("legal_metrology_compliance")]
    compliance=deepcopy(compliance_sources[0]) if compliance_sources else {}
    compliance["checks"]=_merge_checks(image_results)
    compliance=_overall(compliance)
    return {"product_name":pi["value"],"product_name_confidence":pi["confidence"],"product_name_evidence":pi["evidence"],"brand":bi["value"],"brand_confidence":bi["confidence"],"brand_evidence":bi["evidence"],"images_analyzed":len(image_results),"images":[{"image_id":r.get("_image_id"),"filename":r.get("_filename"),"analysis":{k:v for k,v in r.items() if not k.startswith("_")}} for r in image_results],"legal_metrology_compliance":compliance,"fusion":{"strategy":"cross_image_evidence_fusion","source_image_count":len(image_results),"product_identity_conflict":pi.get("conflict",False),"brand_conflict":bi.get("conflict",False)}}
