"""
REST API for the packaged-food label analyzer.

Frontend clients such as Android and Web should communicate
with this API instead of directly importing the analysis engine.
"""

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.analyzer_service import analyze_image
from app.services.product_service import ProductService


app = FastAPI(
    title="Packaged Food Label Analyzer API",
    description=(
        "API for OCR-based packaged-food label analysis "
        "and Legal Metrology compliance screening."
    ),
    version="1.0.0",
)


ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


product_service = ProductService()


class ProductCreateRequest(BaseModel):
    """Request body for creating a product."""

    product_name: str | None = None
    brand: str | None = None
    barcode: str | None = None
    manufacturer: str | None = None


@app.get("/")
def health_check():
    """
    Basic API health check.
    """

    return {
        "success": True,
        "service": "Packaged Food Label Analyzer",
        "status": "running",
        "api_version": "v1",
    }


@app.post("/api/v1/analyze")
async def analyze_label(
    image: UploadFile = File(...),
):
    """
    Analyze an uploaded packaged-food label image.

    The frontend sends an image using multipart/form-data.
    The endpoint returns the structured analysis generated
    by the existing analysis engine.
    """

    filename = image.filename or ""

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image format. "
                "Use JPG, JPEG, PNG or WEBP."
            ),
        )

    try:
        image_bytes = await image.read()

        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded image is empty.",
            )

        with NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:
            temp_file.write(image_bytes)
            temp_path = Path(temp_file.name)

        try:
            result = analyze_image(temp_path)

        finally:
            temp_path.unlink(
                missing_ok=True
            )

        return {
            "success": True,
            "api_version": "v1",
            "data": result,
            "warnings": [],
            "errors": [],
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )


@app.post("/api/v1/products")
def create_product(
    request: ProductCreateRequest,
):
    """
    Create a new product in the repository.
    """

    try:
        product = product_service.create_product(
            product_name=request.product_name,
            brand=request.brand,
            barcode=request.barcode,
            manufacturer=request.manufacturer,
        )

        return {
            "success": True,
            "api_version": "v1",
            "data": product.to_dict(),
            "warnings": [],
            "errors": [],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )


@app.get("/api/v1/products")
def list_products():
    """
    Return all products stored in the repository.
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
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )


@app.get("/api/v1/products/{product_id}")
def get_product(
    product_id: str,
):
    """
    Return a product and its scan history.
    """

    try:
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

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )


@app.get("/api/v1/products/{product_id}/scans")
def get_product_scans(
    product_id: str,
):
    """
    Return the complete scan history of a product.
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

    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Product not found.",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )
@app.get("/api/v1/products/{product_id}/scans/{scan_id}")
def get_product_scan(
    product_id: str,
    scan_id: str,
):
    """
    Return one specific scan belonging to a product.
    """

    try:
        scan = product_service.get_scan(
            product_id=product_id,
            scan_id=scan_id,
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

    except HTTPException:
        raise

    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Product not found.",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

@app.post("/api/v1/products/{product_id}/analyze")
async def analyze_product(
    product_id: str,
    image: UploadFile = File(...),
):
    """
    Analyze an image and store the resulting analysis
    as a scan belonging to an existing product.
    """

    product = product_service.get_product(
        product_id
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found.",
        )

    filename = image.filename or ""

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image format. "
                "Use JPG, JPEG, PNG or WEBP."
            ),
        )

    try:
        image_bytes = await image.read()

        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded image is empty.",
            )

        with NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:
            temp_file.write(image_bytes)
            temp_path = Path(temp_file.name)

        try:
            result = analyze_image(temp_path)

            scan = product_service.add_analysis_scan(
                product_id=product_id,
                image_path=temp_path,
                analysis_result=result,
                image_quality=result.get(
                    "image_quality"
                ),
                ocr=result.get("ocr"),
            )

        finally:
            temp_path.unlink(
                missing_ok=True
            )

        return {
            "success": True,
            "api_version": "v1",
            "data": {
                "product_id": product_id,
                "scan": scan.to_dict(),
            },
            "warnings": [],
            "errors": [],
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )
