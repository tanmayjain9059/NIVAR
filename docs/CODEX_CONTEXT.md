# NIVAR Current Project Context

**Updated:** 2026-09-23  
**Branch:** `semantic-extraction-rewrite`  
**Problem Statement:** SIH26034 — Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.

This file records the current implementation context for future development. **Source code and tests are authoritative.**

## Product goal

NIVAR is an evidence-aware packaged-commodity analysis platform.

The current system:

1. accepts one or more package images;
2. evaluates image quality;
3. preprocesses the images;
4. runs PaddleOCR;
5. preserves OCR text, confidence and geometry;
6. detects relevant label regions;
7. extracts product identity, food-label information and Legal Metrology declarations;
8. validates declarations using evidence-aware statuses;
9. fuses evidence across multiple images;
10. persists products, scans and source images;
11. exposes the result through FastAPI;
12. renders results through the React/Vite frontend.

NIVAR is a preliminary screening tool, not a legal certification system.

## Current architecture

```text
Upload
  ↓
FastAPI
  ↓
Analyzer Service
  ↓
Image Quality
  ↓
OpenCV / preprocessing
  ↓
PaddleOCR
  ↓
OCR text + confidence + bbox
  ↓
Region detection
  ├── Nutrition
  ├── Ingredients
  ├── Allergens
  └── Compliance
  ↓
Semantic extraction
  ├── Product identity
  ├── Food analysis
  └── Legal Metrology
  ↓
Multi-image evidence fusion
  ↓
Structured result
  ├── API
  └── Product repository
        ├── Product
        ├── Scan
        └── Image records
```

## Important implementation facts

### OCR

- Primary OCR: PaddleOCR 3.7.0.
- Runtime: PaddlePaddle 3.2.2.
- OCR language codes currently supported by the API:
  `en, hi, mr, te, ta, ka, sa, bho, mai, gom, bgc`.
- PaddleOCR is configured with document orientation/unwarping/text-line orientation support.
- OCR geometry is retained for evidence and spatial extraction.
- Tesseract remains available as a secondary provider/workflow.

Do not change the PaddleOCR/PaddlePaddle versions casually while extraction behavior is being stabilized.

### Product identity

`src/product_intelligence/identity.py` intentionally uses a relatively simple hierarchy:

1. explicit Product Name / Name of Product / Name of Food label;
2. plausible front-panel candidates;
3. nearby OCR-token joins;
4. ordered global OCR fallback.

Candidates resembling company names, addresses, nutrition, ingredients, compliance declarations or marketing copy are rejected/penalized.

Product identity must remain separate from:

- brand;
- manufacturer;
- manufacturer address;
- marketing copy.

### Food analysis

- `src/food_analysis/nutrition.py` combines spatial and text evidence.
- `ingredients.py` is section-aware and stops at subsequent label sections.
- `allergens.py` conservatively extracts values after Contains/May contain anchors and filters to known allergen terms.

Do not feed arbitrary global marketing text into the ingredient/allergen parsers when a section-specific OCR result exists.

### Compliance

Core checks:

- manufacturer / packer / importer
- net quantity
- manufacture / packing date
- MRP
- consumer-care details

Conditional/manual-review checks include country of origin and generic/common-name handling.

Current statuses:

- `FOUND`
- `REVIEW`
- `NOT_FOUND`

The validator uses evidence and a confidence gate for detected declarations. A low-confidence detection can become `REVIEW`.

Manufacturer extraction keeps the company/entity name separate from address text. If the manufacturer address evidence is missing, the check can remain `REVIEW` rather than falsely reporting a complete declaration.

### Multi-image fusion

A scan accepts up to 8 images.

`src/product_intelligence/fusion.py` combines per-image product identity, food fields, compliance checks and evidence.

Persisted image IDs are reconciled with analysis image entries by scan order in `app/api.py` to avoid provenance drift.

### Persistence

The repository is currently JSON-backed:

- `src/repository/models.py`
- `src/repository/store.py`

`ProductRecord` can contain multiple `ScanRecord` objects.

A scan can contain multiple `ImageRecord` objects and a complete JSON-safe analysis snapshot.

`app/services/product_service.py` copies uploaded images into product-specific storage.

This is suitable for the current development phase but is not the final production database architecture.

### API

Active routes include:

```text
GET  /health
POST /api/v1/analyze
POST /api/v1/products/analyze
GET  /api/v1/products/{product_id}/scans/{scan_id}/images/{image_id}
```

The API enforces:

- JPG/JPEG/PNG/WEBP;
- maximum 8 images;
- maximum 15 MB per image.

FastAPI serves the frontend build when `frontend/dist` exists.

### Frontend

React + TypeScript + Vite.

Current pages:

- Home
- Upload
- Processing
- Results
- History

The Processing page provides the large-image/live-scan presentation. Results exposes structured extraction and compliance evidence. History consumes persisted product/scan data.

## Tests and CI

Regression tests are under `tests/`.

Important suites include:

- `test_extraction_regressions.py`
- `test_fusion_conflicts.py`
- `test_product_fusion.py`
- `test_product_identity.py`
- `test_repository.py`
- `test_semantic_extraction.py`

GitHub Actions workflow:

```text
.github/workflows/validation.yml
  ├── backend-regressions
  │    └── pytest -q tests/test_extraction_regressions.py
  └── frontend-build
       └── npm ci && npm run build
```

CI uses Python 3.11 for the regression suite.

A recent CI failure was caused by a malformed string literal in `src/ocr/engine.py`, not by a failed extraction assertion. That syntax error was repaired in commit `befbf213f5feac604b069f9c56152756000ab0e4`. Always verify the current workflow before claiming CI is green.

## Local development

Repository path used during development:

```text
/Users/tillu/Projects/NIVAR
```

Recommended backend commands:

```bash
source venv/bin/activate
python -m pip install -r requirements.txt
python -m app.main <image-path>
uvicorn app.api:app --reload
```

Recommended frontend commands:

```bash
cd frontend
npm ci
npm run dev
```

## Working rules

1. Prefer complete, coherent feature batches over many micro-patches.
2. For structural changes, inspect the current source before editing.
3. Add regression coverage for extraction behavior.
4. Preserve OCR evidence and source-image provenance.
5. Do not infer missing values from unrelated numbers.
6. Do not hard-code coordinates for a single image.
7. Do not repeatedly run full-image OCR when existing evidence is sufficient.
8. Keep legal rules in the compliance layer.
9. Keep API concerns out of OCR/extraction modules.
10. Treat `FOUND` as detected evidence, not legal certification.
11. Treat `NOT_FOUND` as “not detected,” not proof of physical absence.
12. Verify tests and CI before declaring a change complete.

## Current next priorities

See [TODO.md](TODO.md). The immediate focus is extraction reliability and evidence quality before deeper compliance automation.
