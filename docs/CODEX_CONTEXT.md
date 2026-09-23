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


# Historical development handoff — complete checkpoint timeline

## Checkpoint A — SIH problem selection and framing
NIVAR began from SIH26034, focused on checking packaged-commodity declarations under the Legal Metrology (Packaged Commodities) Rules, 2011. The original concept was broader than OCR: scan packaging, identify mandatory declarations, detect presentation problems, and give an evidence-backed compliance result. Early pitch work emphasized the problem, solution, innovation, technical architecture, feasibility, risk mitigation, impact, scalability and genuine references.

## Checkpoint B — OpenCV + Tesseract prototype
The first practical prototype was developed as an OpenCV/Tesseract label analyzer on macOS. A Tkinter image picker, preprocessing experiments, Tesseract image_to_string/image_to_data, confidence values and bounding boxes were used. Green OCR boxes and automatic regions were introduced to make the result visually understandable.

Real packaging images exposed the first major limitation: OCR can recover text while still failing to understand which text belongs to ingredients, nutrition, allergens or Legal Metrology declarations.

## Checkpoint C — Automatic ROI/section detection
An automatic analyzer was added to locate Ingredients, Nutrition and Allergens sections from OCR headings and coordinates. Example detections included Nutrition around x=387,y=2098 and Ingredients around x=2040,y=2017 on one large sample. This established the need to preserve OCR geometry instead of flattening the result into one text string.

## Checkpoint D — PaddleOCR migration
PaddleOCR became the primary OCR engine because the project needs stronger layout handling, multilingual Indian-language support, orientation handling and unwarping. PaddleOCR 3.7.0 and PaddlePaddle 3.2.2 became the pinned stack. Tesseract remains available as a secondary provider.

Current PaddleOCR settings enable document orientation classification, document unwarping and text-line orientation. OCR results preserve text, confidence, bounding boxes and language, with coordinates mapped back to the original image after resizing.

## Checkpoint E — Real-image extraction
Large real package images were processed, including a 4110×5271 sample. OCR recovered substantial packaging text and the nutrition extractor recovered a complete set of useful nutrition values. This demonstrated that the project could move from OCR into structured food-label extraction.

At the same time, ingredients and allergens were noisy and the first compliance implementation frequently returned NOT_FOUND even when declarations were visually present. This became the central reliability issue.

## Checkpoint F — Semantic extraction architecture
The codebase was separated into OCR, preprocessing, food analysis, product intelligence, compliance, fusion, repository, API and frontend layers. The key architectural decision was that OCR creates evidence while semantic extraction interprets it and the validator applies compliance rules.

Product identity was deliberately simplified after an earlier implementation became over-optimized. The current hierarchy is explicit product-name labels first, then plausible front-panel candidates, joined OCR tokens and ordered global fallback. Manufacturer, address, nutrition, ingredients, compliance text and marketing copy are penalized/rejected as product-name candidates.

## Checkpoint G — Manufacturer/address correction
A real extraction bug selected an address-like OCR value as the manufacturer entity. The extractor was changed so legal/company entities are favored and address indicators, phone numbers, email and PIN codes are penalized. Manufacturer name and address remain separate evidence fields. Missing address evidence can force REVIEW instead of a false complete match.

## Checkpoint H — Compliance validator
The compliance layer was formalized around five core declarations: manufacturer/packer/importer, net quantity, manufacture/packing date, MRP and consumer care. Country of origin and generic/common-name handling are additional conditional/manual-review areas.

The validator uses FOUND, REVIEW and NOT_FOUND. FOUND means detected evidence, REVIEW means incomplete/uncertain evidence, and NOT_FOUND means the current system did not detect evidence. These statuses are deliberately not treated as legal certification.

## Checkpoint I — Multi-image fusion
One package may distribute mandatory information across several faces. The system was therefore extended to accept up to eight images and fuse product identity, food fields, compliance findings, conflicts and evidence. Persisted source-image references are reconciled using scan order so provenance does not drift between analysis and stored images.

## Checkpoint J — Persistence and API
The backend evolved into a FastAPI application with product and scan persistence. Uploaded images are stored under product-specific storage, and analysis snapshots are retained. The API supports health, single/multi-image analysis and persisted scan-image retrieval.

## Checkpoint K — React frontend
The frontend became a React/TypeScript/Vite application with Home, Upload, Processing, Results and History pages. The Processing screen was redesigned around a large image, scanner animation, live-scan indicator, PaddleOCR/NIVAR indicators, thumbnails and pipeline progress.

A frontend issue was reported where the new scanner UI appeared on the first scan but an older UI appeared on later scans. The source build passed, but a true browser-level repeated-scan test has not been established from the available tooling. Therefore this must not be described as fixed merely because CI builds successfully.

## Checkpoint L — Regression tests and CI
Regression tests were introduced for extraction, product identity, multi-image fusion, conflicts, repository behavior and semantic extraction. GitHub Actions runs backend regression tests and a frontend production build.

During development, CI exposed malformed newline string literals in src/ocr/engine.py. Multiple syntax issues were repaired, including the region-text join. This reinforced the project rule that no change should be declared complete without verification.

## Checkpoint M — Current primary blocker
The current blocker is false negatives on the five mandatory declarations. A package can visibly contain the declarations while the final validator reports NOT_FOUND. This must be traced before adding advanced computer-vision features.

The debugging path must be: actual image → raw PaddleOCR lines → bounding boxes → region detection → declaration candidate generation → candidate rejection/confidence → validator. For every declaration, determine whether the text was absent from OCR, excluded by region detection, missed by pattern matching, split across OCR lines, rejected as the wrong semantic candidate, or downgraded by confidence.

Do not solve this by taking the nearest arbitrary number. Packaging contains dates, batch numbers, nutrition values, phone numbers, PIN codes and prices. Candidate extraction must be declaration-specific and evidence-aware.

## Checkpoint N — Curved/cylindrical packaging is a later phase
PaddleOCR already has unwarping enabled, but cylindrical and strongly curved packaging may require an additional cylindrical unwrap or multi-pass OCR strategy. The proposed future approach is original image + unwarped image + cylindrical representation when needed, followed by confidence/text-coverage comparison and evidence fusion. This work should begin only after the five-declaration false-negative problem is understood.

## Current implementation rules
1. Inspect the current repository before changing architecture.
2. Preserve OCR text, confidence, bbox and source-image provenance.
3. Prefer semantic/spatial evidence over exact-string matching.
4. Do not infer declaration values from arbitrary numbers.
5. Do not hard-code coordinates for one package.
6. Keep legal rules in the compliance layer.
7. Keep API code separate from OCR and extraction.
8. Use multi-image fusion for package faces.
9. Add regression tests for every extraction bug fixed.
10. Verify CI and, when relevant, browser/runtime behavior before claiming success.

## Immediate continuation task
Take one real failing image for which the five mandatory declarations are visibly present. Instrument or inspect the existing pipeline to show the OCR lines and bboxes for each declaration. Trace each one through enhanced_extractor and validator. Fix the actual evidence-loss point, add a regression fixture/test, run the backend tests and frontend build, then evaluate whether cylindrical/curved handling is still necessary for that failure.

## Continuation prompt for a new chat
I am continuing NIVAR, repository tanmayjain9059/NIVAR, branch semantic-extraction-rewrite. Read docs/CODEX_CONTEXT.md before doing anything. Do not restart the project or invent a new architecture. The immediate blocker is false negatives: the five mandatory Legal Metrology declarations can be visibly present on a package but NIVAR returns NOT_FOUND. Trace one real failing image through PaddleOCR text/bboxes, region detection, enhanced_extractor, candidate scoring and validator. Identify exactly where evidence is lost, make the smallest robust evidence-aware fix, add regression tests, run tests/CI, and verify before claiming success. Only after that work on curved/bent/cylindrical packaging using PaddleOCR unwarping and, if necessary, cylindrical unwrap/multi-pass OCR.

## Repository links
Context document: https://github.com/tanmayjain9059/NIVAR/blob/semantic-extraction-rewrite/docs/CODEX_CONTEXT.md
Development branch: https://github.com/tanmayjain9059/NIVAR/tree/semantic-extraction-rewrite
