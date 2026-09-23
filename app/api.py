"""
FastAPI application for the packaged-commodity compliance analyzer.

The API layer is intentionally thin:
    request
        -> analysis service
        -> product persistence
        -> structured response

The OCR/compliance logic remains inside the existing analysis pipeline.
"""

from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import (
    File,
    HTTPException,
    UploadFile,
)

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.services.analyzer_service import (
    analyze_image,
    analyze_product_images,
)
from app.services.product_service import ProductService
from src.reporting import generate_pdf_report

# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Packaged Commodity Compliance Analyzer",
    version="1.0.0",
    description=(
        "AI-assisted OCR system for checking packaged "
        "commodity declarations under Legal Metrology "
        "(Packaged Commodities) Rules, 2011."
    ),
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SERVICES
# ============================================================

product_service = ProductService()


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    frontend_index = Path("frontend/dist/index.html")
    if frontend_index.exists():
        return FileResponse(frontend_index)
    return {
        "success": True,
        "api_version": "v1",
        "service": "Packaged Commodity Compliance Analyzer",
        "status": "running",
        "ui": "Frontend build not found. Run npm run dev in frontend or use Docker.",
    }


@app.get("/health")
def health_check():
    return {
        "success": True,
        "api_version": "v1",
        "status": "healthy",
    }


# ============================================================
# IMAGE ANALYSIS
# ============================================================

@app.post("/api/v1/analyze")
@app.post("/api/v1/products/analyze")
async def analyze_product(
    images: list[UploadFile] = File(...),
):
    """
    Analyze multiple images belonging to one packaged product.

    One request represents one product.
    Multiple images are independently analyzed and then
    fused into one product-level result.
    """

    if not images:
        raise HTTPException(
            status_code=400,
            detail="At least one image is required.",
        )

    if len(images) > 8:
        raise HTTPException(
            status_code=400,
            detail=(
                "A maximum of 8 images can be "
                "analyzed in one product scan."
            ),
        )

    temporary_paths = []

    try:
        for image in images:

            filename = image.filename or ""

            extension = Path(
                filename
            ).suffix.lower()

            if extension not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Unsupported image format: "
                        f"{filename}. "
                        "Use JPG, JPEG, PNG or WEBP."
                    ),
                )

            image_bytes = await image.read()

            if not image_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Uploaded image is empty: "
                        f"{filename}"
                    ),
                )

            with NamedTemporaryFile(
                suffix=extension,
                delete=False,
            ) as temp_file:

                temp_file.write(
                    image_bytes
                )

                temporary_paths.append(
                    Path(
                        temp_file.name
                    )
                )

        analysis = analyze_product_images(
            temporary_paths
        )

        import json

        analysis_snapshot = json.loads(
            json.dumps(
                analysis,
                ensure_ascii=False,
                default=str,
            )
        )

        product = product_service.create_product(
            product_name=analysis_snapshot.get(
                "product_name"
            ),
            brand=analysis_snapshot.get(
                "brand"
            ),
            product_name_confidence=(
                analysis_snapshot.get(
                    "product_name_confidence"
                )
            ),
            brand_confidence=(
                analysis_snapshot.get(
                    "brand_confidence"
                )
            ),
        )

        product_service.add_product_scan(
            product_id=product.product_id,
            image_paths=temporary_paths,
            analysis_result=analysis_snapshot,
        )

        return {
            "success": True,
            "api_version": "v1",
            "data": {
                "product_id": product.product_id,
                **analysis_snapshot,
            },
            "warnings": [],
            "errors": [],
        }

    except HTTPException:
        raise

    except (
        FileNotFoundError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Product analysis failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc

    finally:
        for path in temporary_paths:
            path.unlink(
                missing_ok=True
            )
# ============================================================
# PRODUCT HISTORY
# ============================================================

@app.get("/api/v1/products")
def list_products():
    """
    Return all stored products and their scan history.
    """

    try:
        products = product_service.list_products()

        return {
            "success": True,
            "api_version": "v1",
            "data": [
                product.to_dict()
                for product in products
            ],
            "warnings": [],
            "errors": [],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to load products: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@app.get("/api/v1/products/{product_id}")
def get_product(
    product_id: str,
):
    """
    Return one product and its complete scan history.
    """

    product = product_service.get_product(
        product_id
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found.",
        )

    return {
        "success": True,
        "api_version": "v1",
        "data": product.to_dict(),
        "warnings": [],
        "errors": [],
    }


@app.get("/api/v1/products/{product_id}/scans")
def get_scan_history(
    product_id: str,
):
    """
    Return all scans belonging to one product.
    """

    try:
        scans = product_service.get_scan_history(
            product_id
        )

        return {
            "success": True,
            "api_version": "v1",
            "data": [
                scan.to_dict()
                for scan in scans
            ],
            "warnings": [],
            "errors": [],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to load scan history: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


# ============================================================
# SINGLE SCAN DETAILS
# ============================================================

@app.get(
    "/api/v1/products/{product_id}/scans/{scan_id}"
)
def get_scan(
    product_id: str,
    scan_id: str,
):
    """
    Return one complete historical scan.

    The stored analysis is returned directly.
    No OCR or image analysis is performed again.
    """

    product = product_service.get_product(
        product_id
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found.",
        )

    scan = product_service.get_scan(
        product_id,
        scan_id,
    )

    if scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found.",
        )

    return {
        "success": True,
        "api_version": "v1",
        "data": scan.to_dict(),
        "warnings": [],
        "errors": [],
    }


# ============================================================
# STORED SCAN IMAGE
# ============================================================

@app.get(
    "/api/v1/products/{product_id}/scans/{scan_id}/image"
)
def get_scan_image(
    product_id: str,
    scan_id: str,
):
    """
    Return the permanently stored image associated
    with a historical scan.
    """

    product = product_service.get_product(
        product_id
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found.",
        )

    scan = product_service.get_scan(
        product_id,
        scan_id,
    )

    if scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found.",
        )

    image_path = Path(scan.image_path)

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Stored scan image not found.",
        )

    return FileResponse(
        path=image_path,
        filename=image_path.name,
    )

# ============================================================
# PDF REPORT
# ============================================================

@app.get(
    "/api/v1/products/{product_id}/scans/{scan_id}/report"
)
def get_scan_report(
    product_id: str,
    scan_id: str,
):
    """
    Generate a PDF report from an already-persisted scan.

    IMPORTANT:
        This endpoint does NOT run OCR, preprocessing,
        extraction, or compliance validation.

        It only reads the stored ScanRecord and converts
        the existing analysis into a PDF.
    """

    product = product_service.get_product(
        product_id
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found.",
        )

    scan = product_service.get_scan(
        product_id,
        scan_id,
    )

    if scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found.",
        )

    if not isinstance(scan.analysis, dict):
        raise HTTPException(
            status_code=409,
            detail=(
                "This scan does not contain a stored "
                "analysis result and cannot generate a PDF report."
            ),
        )

    image_path = Path(scan.image_path)

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Stored scan image not found.",
        )

    report_dir = Path("results") / "reports"
    report_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_product_id = (
        "".join(
            character
            if character.isalnum() or character in "-_"
            else "_"
            for character in product_id
        )
        or "product"
    )

    safe_scan_id = (
        "".join(
            character
            if character.isalnum() or character in "-_"
            else "_"
            for character in scan_id
        )
        or "scan"
    )

    report_path = (
        report_dir
        / f"{safe_product_id}_{safe_scan_id}_report.pdf"
    )

    try:
        generate_pdf_report(
            analysis=scan.analysis,
            image_path=image_path,
            output_path=report_path,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "PDF report generation failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=(
            f"compliance_report_"
            f"{safe_scan_id}.pdf"
        ),
    )

# Production frontend assets. API routes above keep their /api/* paths.
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")\n