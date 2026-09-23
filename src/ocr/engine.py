"""
Common OCR engine interface for Tesseract and PaddleOCR.
"""
import re
import pandas as pd
import pytesseract
from .provider import create_ocr_engine

def _paddle_result_to_dataframe(result):
    rows=[]
    for line in result.get("lines",[]):
        text=str(line.get("text","")).strip()
        bbox=line.get("bbox")
        if not text or not bbox or len(bbox)!=4: continue
        try:
            x1,y1,x2,y2=(int(v) for v in bbox)
            confidence=float(line.get("confidence",0.0))
        except (TypeError,ValueError): continue
        rows.append({"text":text,"left":x1,"top":y1,"width":max(0,x2-x1),
                     "height":max(0,y2-y1),"right":x2,"bottom":y2,"conf":confidence})
    return pd.DataFrame(rows,columns=["text","left","top","width","height","right","bottom","conf"])

def build_ocr_summary(data,engine_name,language=None):
    confidences=[]
    line_count=0
    if data is not None and not getattr(data,"empty",True):
        line_count=len(data)
        if "conf" in data.columns:
            confidences=pd.to_numeric(data["conf"],errors="coerce").dropna()
            confidences=confidences[confidences>=0].tolist()
    return {"engine":str(engine_name),"language":language,"line_count":line_count,
            "average_confidence":round(sum(confidences)/len(confidences),4) if confidences else None}

def _run_tesseract(image,config):
    data=pytesseract.image_to_data(image,config=config["global_ocr_config"],output_type=pytesseract.Output.DATAFRAME)
    data=data.dropna(subset=["text"])
    data["text"]=data["text"].astype(str).str.strip()
    data=data[data["text"]!=""].copy()
    for column in ("left","top","width","height"): data[column]=data[column].astype(int)
    data["right"]=data["left"]+data["width"]; data["bottom"]=data["top"]+data["height"]
    raw_text=pytesseract.image_to_string(image,config=config["global_ocr_config"])
    return data,raw_text

def _run_paddle(image_path,coordinate_scale=1.0,language="en"):
    if image_path is None: raise ValueError("image_path is required when using PaddleOCR.")
    result=create_ocr_engine("paddle",language=language).extract(image_path)
    data=_paddle_result_to_dataframe(result)
    try: coordinate_scale=float(coordinate_scale)
    except (TypeError,ValueError): coordinate_scale=1.0
    if coordinate_scale<=0: coordinate_scale=1.0
    if coordinate_scale!=1.0 and not data.empty:
        for column in ("left","top","width","height","right","bottom"):
            data[column]=(data[column]*coordinate_scale).round().astype(int)
    raw_text="\n".join(str(line.get("text","")).strip() for line in result.get("lines",[]) if str(line.get("text","")).strip())
    return data,raw_text,result.get("language",language)

def run_ocr(image,config,image_path=None,coordinate_scale=1.0):
    engine_name=str(config.get("ocr_engine","tesseract")).lower().strip()
    if engine_name=="tesseract": return _run_tesseract(image,config)
    if engine_name=="paddle":
        data,raw_text,_=_run_paddle(image_path,coordinate_scale,str(config.get("ocr_lang","en")).lower().strip())
        return data,raw_text
    raise ValueError(f"Unsupported OCR engine: {engine_name}. Use 'tesseract' or 'paddle'.")

def ocr_roi(roi,config):
    if roi is None: return ""
    from .preprocessing import prepare_roi_for_ocr
    cleaned=prepare_roi_for_ocr(roi,config)
    if str(config.get("ocr_engine","tesseract")).lower().strip()=="tesseract":
        return pytesseract.image_to_string(cleaned,config=config["roi_ocr_config"])
    raise NotImplementedError("PaddleOCR ROI OCR is disabled; reuse the global OCR result.")

def clean_word(text): return re.sub(r"[^a-z0-9]","",str(text).lower())

def extract_text_from_region(data,region,min_overlap=0.20):
    if data is None or data.empty or region is None: return ""
    x1,y1=int(region["x"]),int(region["y"]); x2=x1+int(region["w"]); y2=y1+int(region["h"])
    selected=[]
    for _,row in data.iterrows():
        try: left,top,right,bottom=int(row["left"]),int(row["top"]),int(row["right"]),int(row["bottom"])
        except (TypeError,ValueError): continue
        overlap=max(0,min(right,x2)-max(left,x1))*max(0,min(bottom,y2)-max(top,y1))
        area=max(1,(right-left)*(bottom-top))
        if overlap/area<min_overlap: continue
        text=str(row["text"]).strip()
        if text: selected.append((top,left,text))
    selected.sort(key=lambda item:(item[0],item[1]))
    return "\n".join(item[2] for item in selected)
