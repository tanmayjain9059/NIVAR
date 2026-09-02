"""
Tesseract OCR engine.

Returns OCR text together with confidence scores and bounding boxes
so it can be used interchangeably with PaddleOCR.
"""

from pathlib import Path

import pytesseract
from pytesseract import Output


class TesseractOCREngine:
    """Tesseract implementation of the OCR provider interface."""

    def __init__(self, config="--psm 11"):
        self.config = config

    def extract(self, image_path: str | Path) -> dict:
        """Run Tesseract and return normalized OCR lines."""

        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        if not image_path.is_file():
            raise ValueError(
                f"Path is not a file: {image_path}"
            )

        data = pytesseract.image_to_data(
            str(image_path),
            config=self.config,
            output_type=Output.DICT,
        )

        lines = []

        for i, text in enumerate(data["text"]):

            text = text.strip()

            if not text:
                continue

            try:
                confidence = float(
                    data["conf"][i]
                )
            except (ValueError, TypeError):
                confidence = None

            x = int(data["left"][i])
            y = int(data["top"][i])
            width = int(data["width"][i])
            height = int(data["height"][i])

            lines.append(
                {
                    "text": text,
                    "confidence": confidence,
                    "bbox": [
                        x,
                        y,
                        x + width,
                        y + height,
                    ],
                }
            )

        return {
            "engine": "tesseract",
            "lines": lines,
        }