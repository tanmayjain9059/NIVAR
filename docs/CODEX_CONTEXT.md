# Codex Project Context

This document reflects the repository state inspected on 2026-09-03. The project is for **Smart India Hackathon 2026, Problem Statement SIH26034**: a system to screen packaged commodities under the **Legal Metrology (Packaged Commodities) Rules, 2011** by scanning products, images, and labels. It is not legal advice: every compliance result is an OCR-based, first-pass screening result that requires human verification, not legal certification.

## Architecture

The application processes a packaged-food image through this pipeline:

```text
image -> image-quality assessment -> OpenCV preprocessing -> global OCR
      -> region detection from OCR coordinates -> food/compliance extraction
      -> structured JSON -> FastAPI response and optional product/scan persistence
```

`app/main.py` owns orchestration. It returns the original image, processed images, detected regions/ROIs, and `structured_result`. `app/services/analyzer_service.py` is the API-facing adapter that returns only `structured_result`. `app/api.py` owns HTTP concerns and delegates persistence to `app/services/product_service.py`.

## Repository tree

```text
AGENTS.md                         repository change and verification rules
README.md                         project overview and SIH26034 context
requirements.txt                  Python dependencies
main.py                           legacy/top-level entry point
automatic_analyzer.py             legacy/top-level analyzer script
pt1.py                            legacy/top-level experiment script
test_paddle.py                    manual PaddleOCR smoke script
app/
  __init__.py                     application package marker
  api.py                         FastAPI endpoints
  main.py                        analysis-pipeline orchestrator
  services/__init__.py            services package marker
  services/analyzer_service.py   adapter to `process_image`
  services/product_service.py    product/scan service and image storage
src/
  __init__.py                     source package marker
  ocr/                           OCR engines, preprocessing, regions, normalization
    __init__.py
    engine.py, provider.py, paddle_engine.py, tesseract_engine.py
    preprocessing.py, normalizer.py, regions.py
  image_quality/quality.py       pre-OCR image acceptance checks
  image_quality/__init__.py
  food_analysis/                 nutrition, ingredients, allergens
    __init__.py, nutrition.py, ingredients.py, allergens.py
  compliance/                    Legal Metrology rules, extraction, validation
    __init__.py, rules.py, extractor.py, validator.py
  reporting/                     JSON output and debug visualization
    __init__.py, json_report.py, visualization.py
  repository/                    JSON-backed product/scan models and store
    __init__.py, models.py, store.py
data/
  products.json                  current JSON repository data
  product_images/                persistent per-product scan copies
docs/
  CODEX_CONTEXT.md                current developer context
  architecture.md, api.md         currently empty placeholders
images/                          sample image assets
```

## Source-of-truth inventory and status

Current source code and its import/call graph are authoritative. README claims, generated output, older standalone scripts, and planned architecture are not implementation evidence.

```text
.gitignore                         IMPLEMENTED: ignores venv, caches, results, and local images
.DS_Store                          GENERATED: local macOS metadata
AGENTS.md                          IMPLEMENTED: repository working rules
README.md                          DOCUMENTATION: historical/project narrative; parts are stale
requirements.txt                   BROKEN: tracked but empty despite runtime dependencies
main.py                            DEBUG-ONLY: standalone manual OpenCV/Tesseract ROI script
automatic_analyzer.py              EXPERIMENTAL: legacy standalone Tesseract analyzer
pt1.py                             EXPERIMENTAL: separate legacy standalone Tesseract analyzer
test_paddle.py                     DEBUG-ONLY/BROKEN: uses obsolete PaddleOCREngine return shape
app/
  __init__.py                      IMPLEMENTED: package marker
  api.py                           IMPLEMENTED: active FastAPI API
  main.py                          IMPLEMENTED: active analysis pipeline and Tkinter GUI
  services/__init__.py             IMPLEMENTED: package marker
  services/analyzer_service.py     IMPLEMENTED: active API-to-pipeline adapter
  services/product_service.py      IMPLEMENTED: active product/scan service
src/
  __init__.py                      IMPLEMENTED: package marker
  ocr/__init__.py                  IMPLEMENTED: package marker
  ocr/engine.py                    IMPLEMENTED: active OCR adapter and region text filtering
  ocr/provider.py                  IMPLEMENTED: active OCR factory
  ocr/paddle_engine.py             IMPLEMENTED: active PaddleOCR wrapper
  ocr/tesseract_engine.py          PARTIAL: provider-compatible wrapper, not the active Tesseract path
  ocr/preprocessing.py             IMPLEMENTED: active preprocessing utilities
  ocr/regions.py                   IMPLEMENTED: active coordinate-based region detection
  ocr/normalizer.py                DEAD-OR-UNUSED: never imported or called
  image_quality/__init__.py        IMPLEMENTED: public export
  image_quality/quality.py         IMPLEMENTED: active pre-OCR quality gate
  food_analysis/__init__.py        IMPLEMENTED: public exports
  food_analysis/nutrition.py       IMPLEMENTED: active nutrition parsing
  food_analysis/ingredients.py     IMPLEMENTED: active heuristic ingredient parsing
  food_analysis/allergens.py       IMPLEMENTED: active regex allergen parsing
  compliance/__init__.py           IMPLEMENTED: public exports
  compliance/rules.py              IMPLEMENTED: configured declarations
  compliance/extractor.py          IMPLEMENTED: active regex extraction/evidence
  compliance/validator.py          IMPLEMENTED: active conservative validation
  repository/__init__.py           IMPLEMENTED: package marker
  repository/models.py             IMPLEMENTED: active dataclass models
  repository/store.py              IMPLEMENTED: active JSON persistence
  reporting/__init__.py            IMPLEMENTED: public exports
  reporting/json_report.py         IMPLEMENTED: active structured-result and JSON writer
  reporting/visualization.py       IMPLEMENTED: active debug-image writer
data/products.json                 IMPLEMENTED runtime data; currently untracked
data/product_images/...            IMPLEMENTED runtime storage; currently untracked
images/                            LOCAL TEST ASSETS; currently ignored/untracked
results/                           GENERATED/ignored output; includes JSON reports and debug ROIs
venv/                              GENERATED/ignored local virtual environment
```

No backup/copy-named source files were found. Python `__pycache__/` directories are generated and ignored. The physical `results/` tree contains the generated JSON files and matching/debug ROI images enumerated by `find results -type f`; it is not source or test coverage.

`app.api -> app.services.analyzer_service -> app.main.process_image` is the active API path. The root scripts are not imported by that path. `automatic_analyzer.py` and `pt1.py` are both legacy Tesseract analyzers but are not byte-identical.

## OCR implementation

- `app/main.py` sets `CONFIG["ocr_engine"]` to `"paddle"`.
- `src/ocr/provider.py` creates PaddleOCR or Tesseract engines.
- `src/ocr/paddle_engine.py` is the primary wrapper. It resizes very large input images to a maximum side of 2500 pixels for OCR, runs `PaddleOCR.predict`, and scales returned boxes back to original-image coordinates.
- `src/ocr/engine.py` converts normalized PaddleOCR lines into a pandas DataFrame with text, confidence, and bounding-box columns. It then scales those coordinates to match the OpenCV-processed image used for region detection.
- PaddleOCR runs globally once per image. Section text for nutrition, ingredients, allergens, and split compliance blocks is extracted from that single DataFrame with `extract_text_from_region`. Paddle ROI OCR is deliberately disabled.
- Tesseract remains supported as the secondary engine. It runs global OCR with `global_ocr_config` and can perform direct ROI OCR with `roi_ocr_config`.

### Actual PaddleOCR flow

For the active configuration, the flow is:

```text
input image -> quality gate -> OpenCV preprocessing
-> run_ocr(..., image_path=original path)
-> one PaddleOCREngine.extract() / PaddleOCR.predict() call
-> normalized Paddle result -> pandas DataFrame
-> coordinate-based region detection
-> extract_text_from_region(DataFrame, region)
-> food and compliance analysis
```

PaddleOCR is called once by `run_ocr` for one `process_image` call. `app/main.py` never calls `ocr_roi` in its Paddle branch; `ocr_roi` raises `NotImplementedError` for Paddle. This prevents per-ROI Paddle inference. The Tesseract branch is different: it performs global Tesseract OCR for regions and then direct Tesseract ROI OCR.

### OCR modules: decision

- `src/ocr/provider.py` — **KEEP**. It is the active, small factory used by `engine.py` for Paddle selection.
- `src/ocr/engine.py` — **KEEP**. It is the active compatibility layer, DataFrame adapter, Tesseract branch, and region-text filter. Modify only when a specific OCR-contract task requires it.
- `src/ocr/normalizer.py` — **REMOVE later**, not now. `rg` finds no imports or calls, and the active flow bypasses it. Do not merge it speculatively while the OCR-persistence task is next.

### OCR data representation

The active representation after `run_ocr` is a pandas DataFrame with exactly: `text`, `left`, `top`, `width`, `height`, `right`, `bottom`, and `conf`. It preserves text, confidence, and rectangular bounds for both current OCR branches. Pandas is genuinely used by the active region, nutrition, and compliance code through `iterrows`, `empty`, filtering, and column operations.

Recommendation: **keep the DataFrame for the MVP**. It minimizes changes while supporting Tesseract, PaddleOCR, coordinate filtering, confidence, and evidence. A dataclass/list representation is viable only as a later deliberate migration with adapters; creating it now adds churn without solving the next persistence task.

## Preprocessing and coordinate systems

`src/ocr/preprocessing.py` enlarges the OpenCV image by **1.5×** with cubic interpolation, converts it to grayscale, applies CLAHE (`clipLimit=2.0`, `tileGridSize=(8, 8)`), and inverts polarity when the enhanced grayscale mean is below **110**. Tesseract ROI OCR additionally median-denoises with the configured kernel and applies Otsu binary thresholding.

PaddleOCR receives the original image path, optionally internally resizes images whose longest side exceeds 2500 pixels, and converts its boxes back to original-image coordinates. `src/ocr/engine.py` then multiplies those coordinates by the application preprocessing scale (currently 1.5) so they align with the enlarged OpenCV image used for region detection and coordinate-based ROI text extraction.

## Image-quality integration

`src/image_quality/quality.py` runs before preprocessing/OCR. It checks resolution, blur (Laplacian variance), brightness, and contrast. Rejection thresholds are: width or height below **500 pixels**, blur variance below **35**, brightness outside **35–225**, and contrast standard deviation below **18**. Its weighted score is resolution **25%**, blur **35%**, brightness **20%**, and contrast **20%**. An image is accepted only if every check passes.

This is a real hard gate in `process_image`: a rejected image does not reach preprocessing or OCR and returns a review-only `structured_result` with `source_image`, `image_quality`, and an empty compliance check set. The API preserves the normal response envelope (`success`, `api_version`, `data`, `warnings`, `errors`), but the rejected-image `data` schema is narrower than a successful structured result; it is therefore not a fully uniform result contract. Successful results add `image_quality` after `build_structured_result`. The product-analysis endpoint passes that value to `ProductService`, which persists it in `ScanRecord.image_quality`.

## Food-analysis modules

- `src/food_analysis/nutrition.py`: spatial nutrition parsing, preferring OCR bounding-box association when DataFrame data is available. It matches recognized nutrient labels to candidate numeric lines to their right, within a vertical tolerance of `max(120, 1.5 * label height)`, then selects smallest vertical distance followed by horizontal distance. Percentage/RDA lines are excluded. It standardizes Energy to `kcal`, Sodium/Cholesterol to `mg`, and other listed nutrients to `g`; OCR confidence is read but not used to rank candidates. If spatial extraction yields no values, text parsing checks the current and next two lines; missing values are omitted. Generated output evidence records Energy `522.0 kcal` for the relevant test-run outputs. This is a verified historical parsing result from spatial association, not hard-coded or universally expected.
- `src/food_analysis/ingredients.py`: removes the ingredients label, stops at other sections, and splits while preserving commas inside parentheses.
- `src/food_analysis/allergens.py`: extracts `Contains` and `May Contains` declarations.
- `src/ocr/regions.py`: detects the relevant regions using the one global OCR result; it is not a food parser.

## Legal Metrology validator

`src/compliance/rules.py` configures five mandatory declarations: manufacturer/packer/importer, net quantity, manufacture/packing date, MRP, and consumer care. Country of origin is conditional; generic/common commodity name is manual review.

`src/compliance/extractor.py` uses tolerant patterns and attaches OCR text, confidence, and bounding boxes when available. `src/compliance/validator.py` assigns `FOUND`, `REVIEW`, or `NOT_FOUND`, leaves overall status as `REVIEW`, and returns a disclaimer. Label-without-value cases for net quantity and MRP are `REVIEW`. The implementation intentionally does not verify legal correctness, placement, font size, readability, or all conditional applicability. A barcode is not compliance evidence.

`FOUND`/`REVIEW`/`NOT_FOUND` summary optimization is intentionally postponed while the backend foundation is completed. Do not optimize it unless explicitly requested later.

### Implemented scope and limits

- **Mandatory:** manufacturer/packer/importer, net quantity, manufacture/packing date, MRP, consumer care.
- **Conditional:** country of origin. It is `FOUND` when detected and `REVIEW` otherwise because product applicability is not determined.
- **Manual review:** generic/common product name, always `REVIEW` with `detected: null`.
- **Not implemented:** legal correctness, placement, font size, readability, complete conditional applicability, semantic product-name extraction, barcode-based evidence, or legal certification.

For mandatory declarations, a detected label with `value_missing` is `REVIEW`; an undetected declaration is `NOT_FOUND`; otherwise it is `FOUND`. The overall status is always `REVIEW`, never PASS/FAIL. Extractor evidence, when a regex match maps to an OCR row, is `{text, confidence, bbox: {x1, y1, x2, y2}}`. Ingredients and allergens are rule/regex heuristics, not NLP or semantic AI; OCR noise, split lines, wording variations, and region-detection failures can reduce accuracy.

## Product repository and permanent scan-image storage

`src/repository/models.py` defines `ProductRecord` and `ScanRecord`; barcodes are optional metadata. `src/repository/store.py` persists them in JSON at `data/products.json` and keeps repository logic separate from API and analysis code.

`app/services/product_service.py` is responsible for product creation, product lookup, product listing, scan creation, permanent image copying, scan-history retrieval, and individual scan lookup. It copies each analyzed image to `data/product_images/<product_id>/<scan_id>.<extension>` and persists the scan record. If persistence fails after the copy, it removes that newly copied image. This is the intended permanent scan-image location.

## Current REST API endpoints

All endpoint implementations are in `app/api.py`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Health check |
| POST | `/api/v1/analyze` | Analyze an uploaded JPG, JPEG, PNG, or WEBP without storing it as a product scan |
| POST | `/api/v1/products` | Create a product with optional name, brand, barcode, and manufacturer |
| GET | `/api/v1/products` | List stored products |
| GET | `/api/v1/products/{product_id}` | Return a product and its scans |
| GET | `/api/v1/products/{product_id}/scans` | Return scan history |
| GET | `/api/v1/products/{product_id}/scans/{scan_id}` | Return one scan |
| POST | `/api/v1/products/{product_id}/analyze` | Analyze an upload and persist it as that product's scan |

## Verified tests and current sample data

There are currently no formal API test files or test-runner configuration. The API endpoints have been manually smoke-tested with `curl`; these are manual checks, not automated API tests. `test_paddle.py` points to the existing `images/IMG_0981.jpeg`, but its result handling is obsolete and therefore it is not a valid smoke verification as written.

Current repository data contains test product `PROD-63045662AEB7` (`Test Product`, `Test Brand`, barcode `8901234567890`) in `data/products.json`. It has three scans. The two permanent scan files currently present are:

- `data/product_images/PROD-63045662AEB7/SCAN-6567AFA83280.jpg`
- `data/product_images/PROD-63045662AEB7/SCAN-2C10EA309748.jpg`

The oldest scan points to a deleted temporary-system path and is not permanent. The latest verified scan is `SCAN-2C10EA309748` (2026-09-02T23:33:48.034438): its image quality is `accepted=true` with score `99.1`, and its compliance overall status is `REVIEW`. Stored counts are 2 detected, 2 review, and 1 missing of 5 mandatory declarations.

## Known gaps and postponed work

- No automated tests for API, repository, OCR conversion, quality gates, or compliance extraction.
- Documentation placeholders `docs/architecture.md` and `docs/api.md` have no content.
- `requirements.txt` is empty even though the active code imports OpenCV, PaddleOCR, pandas, pytesseract, FastAPI, Pydantic, Pillow, and NumPy.
- `images/IMG_0981.jpeg` exists. However, `test_paddle.py` iterates the current wrapper's result dictionary as though it returned Paddle result objects, so it cannot correctly report recognized lines and is not a valid smoke verification until updated.
- Scan storage currently uses a JSON file, not transactional database storage, and one older record retains a non-permanent temporary path.
- `ScanRecord` already has an `ocr` field, but all current stored scans have `"ocr": null`. The product-analysis API passes `image_quality` but does **not** pass OCR information to `ProductService`.
- The system lacks product-name semantic extraction, placement verification, font-size verification, legal-readability assessment, and full conditional-rule applicability.
- Frontend/dashboard, enforcement reports, and broader product/compliance history features remain future work.

## Next task

```text
compact OCR summary in process_image()
→ attach to structured_result["ocr"]
→ pass through product analysis API
→ ProductService.add_analysis_scan()
→ ScanRecord.ocr
→ GET /api/v1/products/{product_id}/scans/{scan_id}
→ verify persisted result
```

The intended compact payload is `{ "engine": "...", "line_count": ..., "average_confidence": ... }`. Do not implement it in the current task.

## Testing and historical-context audit

There are no formal API test files, test framework configuration, fixtures, or test runner. README provides a `curl` example, and the context records manual curl smoke testing; this is not automated coverage. Existing generated reports provide historical/manual output evidence only and include stale results with `PASS` and `PARTIAL` overall statuses that the current validator cannot produce. Do not use those historical output files to infer the current contract.

Historical/planned capabilities are classified as follows:

| Capability | Current status |
| --- | --- |
| OCR cleaning / preprocessing | IMPLEMENTED (the exact transformations documented above) |
| OCR normalizer module | NOT PRESENT in active flow (unused module exists) |
| NLP/LLM layer | NOT PRESENT |
| perspective correction, sharpening, multilingual OCR | NOT PRESENT |
| additional CV preprocessing beyond current resize/grayscale/CLAHE/polarity and Tesseract ROI denoise/Otsu | NOT PRESENT |
| product history / permanent image storage | IMPLEMENTED via JSON repository and `data/product_images` |
| SQLite/PostgreSQL migration | PLANNED |
| Android/Web frontend | PLANNED; FastAPI boundary is implemented |
| evaluation metrics / formal test suite | NOT PRESENT |

## Active-file responsibility audit

| File | Responsibility and actual implementation | Used by | Status / known issue |
| --- | --- | --- | --- |
| `app/main.py` | Active pipeline, CLI and Tkinter UI; invokes quality, OCR, regions, analysis, reporting. | API service, CLI/GUI | IMPLEMENTED; large mixed orchestration/UI module and saves generated results on every successful run. |
| `app/api.py` | FastAPI envelope, upload validation, temp-file lifecycle, product routes. | Uvicorn/FastAPI | IMPLEMENTED; no formal tests; analysis is synchronous; quality-reject data schema differs from success. |
| `app/services/analyzer_service.py` | Validates a path and returns `process_image(...)["structured_result"]`. | API | IMPLEMENTED. |
| `app/services/product_service.py` | Product CRUD-like access, scan ID creation, permanent image copy, rollback, scan lookup/history. | API | IMPLEMENTED; accepts OCR payload but API does not pass one. |
| `src/ocr/engine.py` | Active DataFrame adaptation, configured OCR dispatch, Tesseract ROI OCR, overlap filter. | `app/main.py`, `regions.py` | IMPLEMENTED. |
| `src/ocr/provider.py` | Creates named OCR wrappers. | `engine.py` | IMPLEMENTED. |
| `src/ocr/paddle_engine.py` | Calls Paddle once, optionally resizes, normalizes boxes to original coordinates. | provider/engine | IMPLEMENTED. |
| `src/ocr/tesseract_engine.py` | Path-based provider-compatible wrapper. | provider only | PARTIAL; active Tesseract branch instead uses private engine helpers. |
| `src/ocr/normalizer.py` | Normalizes a dict result. | none | DEAD-OR-UNUSED. |
| `src/ocr/preprocessing.py` | Global and Tesseract-ROI preprocessing. | main/engine/nutrition | IMPLEMENTED. |
| `src/ocr/regions.py` | OCR-coordinate heuristics for four sections and crops/split. | main | IMPLEMENTED; layout heuristic. |
| `src/image_quality/quality.py` | Pre-OCR measurements and gate report. | main | IMPLEMENTED. |
| `src/food_analysis/nutrition.py` | Spatial then text-fallback nutrition parsing. | main | IMPLEMENTED; confidence unused. |
| `src/food_analysis/ingredients.py` | Heuristic cleanup and comma splitting. | main | IMPLEMENTED; OCR/layout sensitive. |
| `src/food_analysis/allergens.py` | `Contains`/`May Contains` regex extraction. | main | IMPLEMENTED; wording-sensitive. |
| `src/compliance/extractor.py` | Regex declarations and row evidence. | validator | IMPLEMENTED; contains unreachable duplicate consumer-care code after `return`. |
| `src/compliance/rules.py` | Rule configuration. | validator | IMPLEMENTED. |
| `src/compliance/validator.py` | Conservative status report and disclaimer. | main | IMPLEMENTED; overall permanently REVIEW. |
| `src/repository/models.py` | Product/scan dataclasses and JSON conversion. | store/service | IMPLEMENTED. |
| `src/repository/store.py` | JSON loading, saving, product and scan operations. | service | IMPLEMENTED; no transaction/concurrency protection. |
| `src/reporting/json_report.py` | Structured-result builder and generated JSON writer. | main | IMPLEMENTED; does not include OCR summary yet. |
| `src/reporting/visualization.py` | Generated overlays and ROI images. | main | IMPLEMENTED; debug output is always written on successful pipeline runs. |

## Final architecture recommendation and change disposition

Keep the present FastAPI -> service -> analysis -> repository separation, one global Paddle inference, DataFrame OCR representation, coordinate-based filtering, image quality gate, and JSON repository boundary. This is the simplest MVP architecture compatible with Android/Web clients now and a later SQLite/PostgreSQL repository replacement. Do not introduce an OCR dataclass or refactor `app/main.py` now; the compact OCR persistence task is smaller and directly improves the scan API.

| Disposition | Files / scope | MVP decision |
| --- | --- | --- |
| KEEP | active API, service, OCR engine/provider/Paddle wrapper, preprocessing, regions, quality, food, compliance, repository, reporting modules | Needed now. |
| MODIFY next | `app/main.py`, `app/api.py`, `app/services/product_service.py`, `src/reporting/json_report.py` | Only for the explicitly scoped compact OCR-summary persistence task. |
| MODIFY later | `requirements.txt`, `test_paddle.py`, API tests, repository transaction/concurrency behavior | Needed for reliability, not before the next scoped task unless explicitly chosen. |
| REMOVE later | `src/ocr/normalizer.py`; unreachable duplicate block in `extract_consumer_care`; obsolete root scripts after migration confirmation | Not needed by active MVP; do not remove during the next task. |
| MERGE | None now | Do not merge legacy standalone scripts into active modules. |
| CREATE later | formal API/unit tests, database repository implementation, frontend, advanced CV/legal verification | Planned, not implemented. |

## Commands

```sh
# Compile any Python file changed in a future task
python -m py_compile path/to/changed_file.py

# Start the API
uvicorn app.api:app --reload

# Existing PaddleOCR script; its result handling requires correction before it is a valid verification
python test_paddle.py
```
