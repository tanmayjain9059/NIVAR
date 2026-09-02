"""
Common OCR representation.

The rest of the application should consume this format
instead of depending on Tesseract or PaddleOCR internals.
"""


def normalize_ocr_result(
    result: dict,
) -> dict:
    """
    Validate and normalize OCR output.

    Expected format:

    {
        "engine": "paddleocr",
        "lines": [
            {
                "text": "...",
                "confidence": 0.98,
                "bbox": [x1, y1, x2, y2]
            }
        ]
    }
    """

    engine = result.get(
        "engine",
        "unknown",
    )

    normalized_lines = []

    for line in result.get(
        "lines",
        [],
    ):

        text = str(
            line.get("text", "")
        ).strip()

        if not text:
            continue

        confidence = line.get(
            "confidence"
        )

        if confidence is not None:
            confidence = float(
                confidence
            )

        bbox = line.get(
            "bbox"
        )

        if bbox is not None:
            bbox = [
                int(value)
                for value in bbox
            ]

        normalized_lines.append(
            {
                "text": text,
                "confidence": confidence,
                "bbox": bbox,
            }
        )

    return {
        "engine": engine,
        "lines": normalized_lines,
        "text": "\n".join(
            line["text"]
            for line in normalized_lines
        ),
    }