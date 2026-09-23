# NIVAR Architecture

## System boundary

```text
Client
  │
  ▼
FastAPI
  │
  ▼
Analyzer Service
  │
  ├── Image Quality
  ├── Preprocessing
  ├── PaddleOCR
  ├── Region Detection
  ├── Food Analysis
  ├── Compliance Extraction
  ├── Product Identity
  └── Evidence Fusion
  │
  ▼
Structured Product Result
  │
  ├── API response
  └── Product Repository
       ├── Product
       ├── Scan
       └── Image records
```

The frontend consumes the API and does not import Python analysis modules.

## Backend layers

### API

**`app/api.py`**

Responsibilities:

- validate uploads
- enforce image count and size limits
- normalize OCR language
- invoke product analysis
- persist product and scan results
- expose stored scan images
- serve the built frontend

OCR and legal-rule logic remain outside the API layer.

### Services

**`app/services/`**

- `analyzer_service.py` coordinates analysis.
- `product_service.py` connects analysis results to persistence and permanent image storage.

### OCR

**`src/ocr/`**

Responsibilities:

- preprocessing
- OCR provider abstraction
- PaddleOCR execution
- OCR normalization
- region detection
- text, confidence and bounding-box handling

PaddleOCR is the primary runtime. Geometry is preserved because compliance evidence and future layout checks depend on spatial relationships.

### Food analysis

**`src/food_analysis/`**

Responsibilities:

- nutrition extraction
- section-scoped ingredient parsing
- conservative allergen extraction

When a relevant section is detected, parsers should prefer that section rather than blindly consuming all package text.

### Compliance

**`src/compliance/`**

Responsibilities:

- declaration extraction
- mandatory/conditional rule definitions
- evidence association
- validation

Core supported declaration checks:

1. manufacturer / packer / importer
2. net quantity
3. manufacture / packing date
4. MRP
5. consumer-care details

Additional conditional/manual-review checks are kept separate.

### Product intelligence

**`src/product_intelligence/`**

Responsibilities:

- product-name and brand extraction
- cross-image identity selection
- multi-image evidence fusion
- conflict preservation

Product identity is intentionally distinct from brand, manufacturer and address.

### Repository

**`src/repository/`**

Responsibilities:

- product records
- scan records
- image records
- persisted analysis snapshots
- product/scan history

The current repository is JSON-backed and replaceable by a database layer later.

## Multi-image flow

A scan can contain up to eight images.

```text
Image 1 ─┐
Image 2 ─┤
Image 3 ─┤
...      ├──► per-image analysis
Image N ─┘          │
                    ▼
              evidence fusion
                    │
                    ▼
             product-level result
```

Each persisted image has its own image ID and can retain image-level analysis/provenance.

The API reconciles analysis image entries with persisted image records by stable scan order so source URLs do not depend on transient OCR identifiers.

## Evidence flow

```text
OCR observation
    │
    ├── text
    ├── confidence
    ├── bbox
    └── source image
          │
          ▼
candidate extraction
          │
          ▼
validation
          │
          ▼
FOUND / REVIEW / NOT_FOUND
          │
          ▼
structured evidence
```

NIVAR prefers evidence over assumptions. If a required value cannot be established, the system should preserve uncertainty instead of borrowing an unrelated number.

## Compliance semantics

The validator currently follows these principles:

- missing detection → `NOT_FOUND`
- incomplete/insufficient evidence → `REVIEW`
- detected evidence above the current confidence gate → `FOUND`
- unresolved review conditions can keep the overall result at `REVIEW`
- the result is a screening output, not legal certification

The confidence gate is an implementation rule for evidence handling; it is not a statement of legal sufficiency.

## Frontend

The frontend is React + TypeScript + Vite.

Major pages:

- Home
- Upload
- Processing
- Results
- History

The API client lives under `frontend/src/api/`.

## Persistence model

```text
Product
│
├── product_id
├── product_name
├── brand
├── barcode (optional)
├── manufacturer
│
└── scans[]
     │
     ├── scan_id
     ├── timestamp
     ├── images[]
     │    ├── image_id
     │    ├── filename
     │    ├── image_path
     │    └── analysis
     └── analysis
```

A scan stores a JSON-safe analysis snapshot so History can reconstruct the result without rerunning OCR.

## CI boundary

```text
Git push
   │
   └── GitHub Actions
       ├── backend-regressions
       │    └── pytest -q tests/test_extraction_regressions.py
       └── frontend-build
            └── npm ci && npm run build
```

CI validates deterministic regression/build behavior; it does not replace real-image evaluation.

## Architectural constraints

- Do not run full-image OCR repeatedly when existing OCR evidence can be reused.
- Do not move legal rules into frontend code.
- Do not infer missing values from unrelated numbers.
- Do not use product-identity heuristics as manufacturer extraction.
- Preserve source-image provenance.
- Add regression coverage before changing established extraction semantics.
