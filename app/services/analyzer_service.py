"""
Analysis service layer.
"""

from pathlib import Path
from time import perf_counter
from uuid import uuid4

from app.main import CONFIG, process_image
from src.product_intelligence import fuse_image_analyses


def _analysis_config(language: str) -> dict:
    language = (language or "en").strip().lower()
    return {
        **CONFIG,
        "ocr_lang": language,
        "show_gui": False,
    }


def analyze_image(file_path: str | Path, language: str = "en") -> dict:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    started = perf_counter()
    result = process_image(str(path), _analysis_config(language))
    if not result:
        raise RuntimeError("Image analysis returned no result.")

    structured = result["structured_result"]
    elapsed_ms = round((perf_counter() - started) * 1000)
    structured.setdefault("meta", {})
    structured["meta"]["analysis_time_ms"] = elapsed_ms
    structured["meta"]["ocr_language"] = language
    return structured


def analyze_product_images(
    file_paths: list[str | Path],
    language: str = "en",
) -> dict:
    if not file_paths:
        raise ValueError("At least one image is required.")

    started = perf_counter()
    image_results = []

    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file does not exist: {path}")

        result = analyze_image(path, language=language)
        image_results.append({
            **result,
            "_image_id": f"IMG-{uuid4().hex[:12].upper()}",
            "_filename": path.name,
        })

    fused = fuse_image_analyses(image_results)
    fused.setdefault("meta", {})
    fused["meta"]["analysis_time_ms"] = round((perf_counter() - started) * 1000)
    fused["meta"]["ocr_language"] = language
    return fused
