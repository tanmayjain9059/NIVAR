"""Geometry-aware nutrition extraction with safe text fallback."""
import re

NUTRIENTS=["Energy","Protein","Carbohydrate","Total Sugars","Added Sugars","Dietary Fiber","Total Fat","Saturated Fat","Trans Fat","Cholesterol","Sodium"]

def _clean(x): return re.sub(r"[^a-z]","",str(x or "").lower())
def _unit(n): return "kcal" if n=="Energy" else ("mg" if n in {"Sodium","Cholesterol"} else "g")
def _numbers(x): return [float(v) for v in re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?",str(x or ""))]
def _label(x,n):
    a,b=_clean(x),_clean(n)
    if a==b: return True
    if a.startswith(b): return a[len(b):] in {"g","mg","kcal","g100g","mg100g","kcal100g"}
    return False

def _rows(df):
    if df is None or getattr(df,"empty",True): return []
    out=[]
    for _,r in df.iterrows():
        text=str(r.get("text","")).strip()
        if not text: continue
        try:
            left,top,right,bottom=map(float,(r["left"],r["top"],r["right"],r["bottom"]))
        except (KeyError,TypeError,ValueError): continue
        out.append({"text":text,"left":left,"top":top,"right":right,"bottom":bottom,"cx":(left+right)/2,"cy":(top+bottom)/2,"h":max(1,bottom-top)})
    return out

def _same_row(a,b):
    overlap=min(a["bottom"],b["bottom"])-max(a["top"],b["top"])
    return overlap>=.2*min(a["h"],b["h"]) or abs(a["cy"]-b["cy"])<=max(.55*max(a["h"],b["h"]),25)

def _spatial(df):
    rows=_rows(df); result={}
    for nutrient in sorted(NUTRIENTS,key=len,reverse=True):
        labels=[r for r in rows if _label(r["text"],nutrient)]
        if not labels: continue
        label=labels[0]
        inline=re.search(re.escape(nutrient)+r"[^0-9]{0,20}(\d+(?:\.\d+)?)",label["text"],re.I)
        if inline:
            result[nutrient]={"value":float(inline.group(1)),"unit":_unit(nutrient)}; continue
        candidates=[]
        for row in rows:
            if row is label or row["left"]<label["right"]-5 or not _numbers(row["text"]) or not _same_row(label,row): continue
            # A percentage token is allowed only when a non-percentage value is also present.
            if "%" in row["text"] and len(_numbers(row["text"]))==1: continue
            gap=row["left"]-label["right"]
            if gap>max(4*label["h"],120): continue
            candidates.append((abs(row["cy"]-label["cy"])*4+gap,row))
        if candidates:
            _,row=min(candidates,key=lambda x:x[0])
            result[nutrient]={"value":_numbers(row["text"])[0],"unit":_unit(nutrient)}
    return result

def parse_nutrition_text(text,ocr_data=None):
    lines=[x.strip() for x in str(text or "").splitlines() if x.strip()]
    spatial=_spatial(ocr_data) if ocr_data is not None else {}
    if not lines and not spatial:
        return {}
    result={}
    ordered=sorted(NUTRIENTS,key=len,reverse=True)
    for i,line in enumerate(lines):
        n=next((x for x in ordered if _label(line,x)),None)
        if not n: continue
        values=_numbers(line)
        # Remove trailing RDA percentages when another value exists.
        if "%" in line and len(values)>1: values=values[:1]
        if not values:
            for nxt in lines[i+1:i+3]:
                if any(_label(nxt,o) for o in ordered if o!=n): break
                values=_numbers(nxt)
                if values: break
        if values and n not in result:
            result[n]={"value":values[0],"unit":_unit(n)}
    # Spatial OCR is preferred where available, but text parsing fills
    # nutrients that geometry could not associate reliably.
    for nutrient,item in spatial.items():
        result[nutrient]=item
    return result

def parse_nutrition_table(roi,config):
    if roi is None: return {}
    import pytesseract
    from src.ocr.preprocessing import prepare_roi_for_ocr
    cleaned=prepare_roi_for_ocr(roi,config)
    text=pytesseract.image_to_string(cleaned,config=config["roi_ocr_config"])
    return parse_nutrition_text(text)
