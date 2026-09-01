"""
REST API for the packaged-food label analyzer.

Frontend clients such as Android and Web should communicate
with this API instead of directly importing the analysis engine.
"""

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.services.analyzer_service import analyze_image


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
    image: UploadFile = File(...)
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

            temp_path = Path(
                temp_file.name
            )

        try:

            result = analyze_image(
                temp_path
            )

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