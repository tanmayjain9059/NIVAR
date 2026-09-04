# Codex Repository Instructions

Before making any repository change, read [`docs/CODEX_CONTEXT.md`](docs/CODEX_CONTEXT.md) in full.

Treat the current Python source code and its import/call graph as the source of truth for implementation status. README claims, generated `results/`, older scripts, and planned architecture notes are not evidence that a feature is implemented.

## Change discipline

- Preserve existing working behavior.
- Make small, modular changes. Do not rewrite a working module unnecessarily.
- Work on one change at a time; verify it before starting the next change.
- Extend the active working path; do not refactor it merely to reconcile legacy or experimental scripts.
- Keep responsibilities separate:
  - `src/ocr/`: OCR providers, preprocessing, normalization, and region text handling.
  - `src/image_quality/`: image acceptance checks only.
  - `src/food_analysis/`: nutrition, ingredients, and allergens only.
  - `src/compliance/`: Legal Metrology extraction, rules, and screening only.
  - `app/api.py`: HTTP request/response handling only.
  - `app/services/`: orchestration between API, analysis, and persistence.
  - `src/repository/`: product and scan persistence only.
- PaddleOCR is the primary engine; Tesseract is the secondary/fallback-compatible engine.
- For PaddleOCR, run global OCR once and reuse its text and bounding boxes for ROIs. Do not run PaddleOCR once per ROI.
- A barcode is product metadata only. Never use it as Legal Metrology compliance evidence.
- Never describe automated results as legal certification, a legal determination, or proof of compliance. Maintain the first-pass/manual-review disclaimer.
- `FOUND`/`REVIEW`/`NOT_FOUND` count optimization is intentionally postponed while the backend foundation is completed. Do not change that logic unless explicitly requested later.

## Verification discipline

- Compile every changed Python file before running its tests:

  ```sh
  python -m py_compile path/to/changed_file.py
  ```

- Then run the smallest relevant test or verification command. Do not claim a check passed unless it was run successfully.
- In handoff notes, give exact repository-relative file paths and exact commands used.

## Current commands

```sh
# Compile a changed module
python -m py_compile app/api.py

# Run the FastAPI server
uvicorn app.api:app --reload

# Legacy PaddleOCR script; its current result handling is obsolete, so do not use it as verification
python test_paddle.py
```
