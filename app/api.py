"""
FastAPI application for NIVAR packaged-commodity analysis.
"""

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.services.analyzer_service import analyze_product_images
from app.services.product_service import ProductService


app=FastAPI(
    title="NIVAR Packaged Commodity Compliance Analyzer",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

product_service=ProductService()

# Serve the Vite production bundle from the same FastAPI origin.
# API routes are registered before this mount so /api/* remains available.
BASE_DIR=Path(__file__).resolve().parent.parent
FRONTEND_DIST=BASE_DIR/"frontend"/"dist"
FRONTEND_ASSETS=FRONTEND_DIST/"assets"
if FRONTEND_ASSETS.is_dir():
    app.mount("/assets",StaticFiles(directory=FRONTEND_ASSETS,html=False),name="frontend-assets")

ALLOWED_EXTENSIONS={".jpg",".jpeg",".png",".webp"}
MAX_UPLOAD_MB=15
SUPPORTED_LANGUAGES={"en","hi","mr","te","ta","ka","sa","bho","mai","gom","bgc"}


@app.get("/")
def root():
    frontend_index=FRONTEND_DIST/"index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    return {
        "success":True,
        "api_version":"v1",
        "service":"NIVAR",
        "status":"running",
        "ui":"Frontend build not found. Run npm run build in frontend.",
    }


@app.get("/health")
def health_check():
    return {"success":True,"api_version":"v1","status":"healthy"}


@app.get("/api/v1/products/{product_id}/scans/{scan_id}/images/{image_id}")
def get_scan_image(product_id:str,scan_id:str,image_id:str):
    scan=product_service.get_scan(product_id,scan_id)
    if scan is None:
        raise HTTPException(status_code=404,detail="Scan not found.")

    for image in getattr(scan,"images",[]) or []:
        if getattr(image,"image_id",None)==image_id:
            path=Path(image.image_path)
            if not path.is_absolute():
                path=BASE_DIR/path
            if not path.exists():
                raise HTTPException(status_code=404,detail="Stored image not found.")
            return FileResponse(path)

    raise HTTPException(status_code=404,detail="Image not found.")


@app.post("/api/v1/analyze")
@app.post("/api/v1/products/analyze")
async def analyze_product(
    images:list[UploadFile]=File(...),
    language:str=Form("en"),
):
    if not images:
        raise HTTPException(status_code=400,detail="At least one image is required.")
    if len(images)>8:
        raise HTTPException(status_code=400,detail="A maximum of 8 images can be analyzed in one product scan.")

    language=language.strip().lower()
    if language not in SUPPORTED_LANGUAGES:
        language="en"

    temporary_paths=[]

    try:
        for image in images:
            filename=image.filename or ""
            extension=Path(filename).suffix.lower()

            if extension not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported image format: {filename}. Use JPG, JPEG, PNG or WEBP.",
                )

            image_bytes=await image.read()
            if not image_bytes:
                raise HTTPException(status_code=400,detail=f"Uploaded image is empty: {filename}")
            if len(image_bytes)>MAX_UPLOAD_MB*1024*1024:
                raise HTTPException(status_code=400,detail=f"{filename} exceeds {MAX_UPLOAD_MB} MB.")

            with NamedTemporaryFile(suffix=extension,delete=False) as temp_file:
                temp_file.write(image_bytes)
                temporary_paths.append(Path(temp_file.name))

        analysis=analyze_product_images(temporary_paths,language=language)

        import json
        analysis_snapshot=json.loads(
            json.dumps(analysis,ensure_ascii=False,default=str)
        )

        product=product_service.create_product(
            product_name=analysis_snapshot.get("product_name"),
            brand=analysis_snapshot.get("brand"),
            product_name_confidence=analysis_snapshot.get("product_name_confidence"),
            brand_confidence=analysis_snapshot.get("brand_confidence"),
        )

        scan=product_service.add_product_scan(
            product_id=product.product_id,
            image_paths=temporary_paths,
            analysis_result=analysis_snapshot,
        )

        source_urls=[]
        for image in getattr(scan,"images",[]) or []:
            source_urls.append({
                "image_id":image.image_id,
                "filename":image.filename,
                "source_url":f"/api/v1/products/{product.product_id}/scans/{scan.scan_id}/images/{image.image_id}",
            })

        # Reconcile transient OCR image IDs with the persisted image records
        # by stable scan order. This prevents provenance/image-link drift.
        analysis_images=analysis_snapshot.get("images",[])
        for index, entry in enumerate(analysis_images):
            if index >= len(source_urls):
                break
            entry.update(source_urls[index])
            entry["analysis"] = entry.get("analysis", {})

        if source_urls:
            analysis_snapshot["source_image"]=source_urls[0]["source_url"]
        analysis_snapshot["scan_id"]=scan.scan_id
        analysis_snapshot["ocr_language"]=language

        return {
            "success":True,
            "api_version":"v1",
            "data":{
                "product_id":product.product_id,
                **analysis_snapshot,
            },
            "warnings":[],
            "errors":[],
        }

    except HTTPException:
        raise
    except (FileNotFoundError,ValueError) as exc:
        raise HTTPException(status_code=400,detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Product analysis failed: {type(exc).__name__}: {exc}",
        ) from exc
    finally:
        for path in temporary_paths:
            path.unlink(missing_ok=True)
