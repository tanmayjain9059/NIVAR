"""
OCR provider factory.
"""
from .paddle_engine import PaddleOCREngine, SUPPORTED_LANGUAGES
from .tesseract_engine import TesseractOCREngine

def create_ocr_engine(name: str = "paddle", language: str = "en"):
    name = name.lower().strip()
    if name == "paddle":
        return PaddleOCREngine(
            lang=language if language in SUPPORTED_LANGUAGES else "en"
        )
    if name == "tesseract":
        return TesseractOCREngine()
    raise ValueError(f"Unsupported OCR engine: {name}")
