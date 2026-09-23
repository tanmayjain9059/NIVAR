"""
PaddleOCR engine for packaged-food label analysis.

The model is cached per language so multi-image scans do not reload a
heavyweight model for every image.
"""

from functools import lru_cache
from pathlib import Path
import tempfile

import cv2
from paddleocr import PaddleOCR

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi / Devanagari",
    "mr": "Marathi / Devanagari",
    "te": "Telugu",
    "ta": "Tamil",
    "ka": "Kannada",
    "sa": "Sanskrit / Devanagari",
    "bho": "Bhojpuri / Devanagari",
    "mai": "Maithili / Devanagari",
    "gom": "Konkani / Devanagari",
    "bgc": "Haryanvi / Devanagari",
}

@lru_cache(maxsize=16)
def _get_paddle(lang: str) -> PaddleOCR:
    return PaddleOCR(
        lang=lang,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )

class PaddleOCREngine:
    def __init__(self, lang: str = "en", max_side: int = 2400):
        self.lang = lang if lang in SUPPORTED_LANGUAGES else "en"
        self.max_side = max_side
        self.ocr = _get_paddle(self.lang)

    def _prepare_image(self, image_path: Path):
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        height, width = image.shape[:2]
        current_max = max(width, height)

        if current_max <= self.max_side:
            return image_path, None, 1.0, 1.0

        scale = self.max_side / current_max
        new_width = max(1, int(width * scale))
        new_height = max(1, int(height * scale))

        resized = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA,
        )

        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()

        if not cv2.imwrite(str(temp_path), resized):
            raise RuntimeError("Failed to create resized OCR image.")

        return temp_path, temp_path, width / new_width, height / new_height

    @staticmethod
    def _scale_bbox(bbox, scale_x, scale_y):
        if not bbox or len(bbox) != 4:
            return None
        x1, y1, x2, y2 = bbox
        return [
            int(round(x1 * scale_x)),
            int(round(y1 * scale_y)),
            int(round(x2 * scale_x)),
            int(round(y2 * scale_y)),
        ]

    def extract(self, image_path: str | Path) -> dict:
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        if not image_path.is_file():
            raise ValueError(f"Image path is not a file: {image_path}")

        ocr_path, temporary_path, scale_x, scale_y = self._prepare_image(image_path)

        try:
            raw_results = self.ocr.predict(str(ocr_path))
            lines = []

            for result in raw_results:
                raw = result.json() if callable(result.json) else result.json
                data = raw.get("res", raw)

                texts = data.get("rec_texts", [])
                scores = data.get("rec_scores", [])
                boxes = data.get("rec_boxes", [])

                for text, score, box in zip(texts, scores, boxes):
                    text = str(text).strip()
                    if not text:
                        continue

                    bbox = self._scale_bbox(box, scale_x, scale_y)
                    if bbox is None:
                        continue

                    try:
                        confidence = float(score)
                    except (TypeError, ValueError):
                        confidence = 0.0

                    lines.append({
                        "text": text,
                        "confidence": confidence,
                        "bbox": bbox,
                        "language": self.lang,
                    })

            return {
                "engine": "paddleocr",
                "language": self.lang,
                "language_name": SUPPORTED_LANGUAGES[self.lang],
                "lines": lines,
                "coordinate_system": "original_image",
            }
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
