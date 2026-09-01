from src.ocr.paddle_engine import PaddleOCREngine

IMAGE = "images/IMG_0981.jpeg"

print("Initializing PaddleOCR...")
engine = PaddleOCREngine()

print("Running OCR...")
results = engine.extract(IMAGE)

print("\n" + "=" * 60)
print("PADDLEOCR TEXT")
print("=" * 60)

for result in results:
    texts = getattr(result, "rec_texts", [])
    scores = getattr(result, "rec_scores", [])

    for text, score in zip(texts, scores):
        print(f"{score:.2f}  |  {text}")

print("=" * 60)
print(f"Detected text lines: {sum(len(getattr(r, 'rec_texts', [])) for r in results)}")
