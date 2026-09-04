"""
Analysis service layer.

This module connects the API/repository layer
with the existing image analysis pipeline.
"""

from pathlib import Path

from app.main import CONFIG, process_image


def analyze_image(file_path: str | Path) -> dict:
    """
    Analyze one packaged-food label image.

    Returns the structured analysis result generated
    by the existing analysis pipeline.
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