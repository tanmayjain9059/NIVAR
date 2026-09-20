"""
Analysis service layer.

Connects API requests with the existing analysis pipeline
and the product-level cross-image fusion layer.
"""

from pathlib import Path
from uuid import uuid4

from app.main import CONFIG, process_image
from src.product_intelligence import (
    fuse_image_analyses,
)


def analyze_image(
    file_path: str | Path,
) -> dict:
    """
    Analyze one packaged-food label image.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Image file does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {path}"
        )

    result = process_image(
        str(path),
        CONFIG,
    )

    if not result:
        raise RuntimeError(
            "Image analysis returned no result."
        )

    return result["structured_result"]


def analyze_product_images(
    file_paths: list[str | Path],
) -> dict:
    """
    Analyze multiple images and fuse them into one
    product-level result.
    """

    if not file_paths:
        raise ValueError(
            "At least one image is required."
        )

    image_results = []

    for file_path in file_paths:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Image file does not exist: {path}"
            )

        result = analyze_image(path)

        image_results.append(
            {
                **result,
                "_image_id": (
                    f"IMG-{uuid4().hex[:12].upper()}"
                ),
                "_filename": path.name,
            }
        )

    return fuse_image_analyses(
        image_results
    )