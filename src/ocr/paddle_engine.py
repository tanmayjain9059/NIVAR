"""
PaddleOCR engine for packaged-food label analysis.

PaddleOCR receives a resized image for performance, but all
returned bounding boxes are converted back to the coordinates
of the original image.
"""

from pathlib import Path
import tempfile

import cv2
from paddleocr import PaddleOCR


class PaddleOCREngine:
    """Lightweight PaddleOCR wrapper."""

    def __init__(
        self,
        lang: str = "en",
        max_side: int = 2500,
    ):
        self.max_side = max_side

        self.ocr = PaddleOCR(
            lang=lang,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

    # ========================================================
    # IMAGE PREPARATION
    # ========================================================

    def _prepare_image(self, image_path: Path):
        """
        Prepare a smaller image for PaddleOCR.

        Returns:
            ocr_path
            temporary_path
            scale_x
            scale_y
        """

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            raise ValueError(
                f"Could not read image: {image_path}"
            )

        height, width = image.shape[:2]

        current_max = max(
            width,
            height,
        )

        # No resize required
        if current_max <= self.max_side:
            return (
                image_path,
                None,
                1.0,
                1.0,
            )

        scale = (
            self.max_side
            / current_max
        )

        new_width = max(
            1,
            int(width * scale),
        )

        new_height = max(
            1,
            int(height * scale),
        )

        resized = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA,
        )

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".jpg",
            delete=False,
        )

        temp_path = Path(
            temp_file.name
        )

        temp_file.close()

        success = cv2.imwrite(
            str(temp_path),
            resized,
        )

        if not success:
            raise RuntimeError(
                "Failed to create resized OCR image."
            )

        # Coordinates from resized image → original image
        scale_x = width / new_width
        scale_y = height / new_height

        print(
            f"PaddleOCR image resized: "
            f"{width}x{height} → "
            f"{new_width}x{new_height}"
        )

        return (
            temp_path,
            temp_path,
            scale_x,
            scale_y,
        )

    # ========================================================
    # BBOX CONVERSION
    # ========================================================

    @staticmethod
    def _scale_bbox(
        bbox,
        scale_x,
        scale_y,
    ):
        """
        Convert a bounding box from resized-image
        coordinates back to original-image coordinates.
        """

        if not bbox or len(bbox) != 4:
            return None

        x1, y1, x2, y2 = bbox

        return [
            int(round(x1 * scale_x)),
            int(round(y1 * scale_y)),
            int(round(x2 * scale_x)),
            int(round(y2 * scale_y)),
        ]

    # ========================================================
    # OCR
    # ========================================================

    def extract(
        self,
        image_path: str | Path,
    ) -> dict:
        """
        Run PaddleOCR and return normalized OCR output.

        Returned bounding boxes always correspond to the
        original image coordinates.
        """

        image_path = Path(
            image_path
        )

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        if not image_path.is_file():
            raise ValueError(
                f"Image path is not a file: {image_path}"
            )

        (
            ocr_path,
            temporary_path,
            scale_x,
            scale_y,
        ) = self._prepare_image(
            image_path
        )

        try:

            print(
                f"Running PaddleOCR on: "
                f"{ocr_path}"
            )

            raw_results = self.ocr.predict(
                str(ocr_path)
            )

            lines = []

            for result in raw_results:

                raw = (
                    result.json()
                    if callable(result.json)
                    else result.json
                )

                data = raw.get(
                    "res",
                    raw,
                )

                texts = data.get(
                    "rec_texts",
                    [],
                )

                scores = data.get(
                    "rec_scores",
                    [],
                )

                boxes = data.get(
                    "rec_boxes",
                    [],
                )

                for text, score, box in zip(
                    texts,
                    scores,
                    boxes,
                ):

                    text = str(
                        text
                    ).strip()

                    if not text:
                        continue

                    bbox = self._scale_bbox(
                        box,
                        scale_x,
                        scale_y,
                    )

                    if bbox is None:
                        continue

                    lines.append(
                        {
                            "text": text,
                            "confidence": float(
                                score
                            ),
                            "bbox": bbox,
                        }
                    )

            return {
                "engine": "paddleocr",
                "lines": lines,
                "coordinate_system": "original_image",
            }

        finally:

            if temporary_path is not None:

                try:
                    temporary_path.unlink(
                        missing_ok=True
                    )
                except Exception:
                    pass