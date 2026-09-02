"""
Service layer for the packaged-food label analyzer.

This module provides a stable interface between the API/frontend
and the internal analysis engine.

The API should call this service instead of directly depending
on OCR, compliance, or food-analysis modules.
"""

from pathlib import Path

from app.main import process_image, CONFIG


def analyze_image(file_path: str | Path) -> dict:
    """
    Analyze a packaged-food label image.

    Parameters
    ----------
    file_path:
        Path to the uploaded image.

    Returns
    -------
    dict
        Structured analysis result produced by the analysis engine.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Image file not found: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Provided path is not a file: {path}"
        )

    result = process_image(
        str(path),
        CONFIG,
    )

    if not result:
        raise RuntimeError(
            "Analysis engine returned no result."
        )

    return result["structured_result"]