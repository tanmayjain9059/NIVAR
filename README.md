# NIVAR

> **NIVAR** — an evidence-aware AI system for scanning packaged commodities and performing preliminary Legal Metrology compliance screening.

NIVAR is being developed for **Smart India Hackathon 2026, Problem Statement SIH26034**:

> Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.

The current implementation combines **computer vision, PaddleOCR, spatial OCR evidence, structured extraction, food-label analysis, rule-based validation, product/scan persistence, and a React web UI**.

NIVAR is intentionally a **first-pass screening system**, not a legal certification or enforcement decision engine.

## What NIVAR does

```text
Package images
     ↓
Image quality assessment
     ↓
OpenCV preprocessing
     ↓
PaddleOCR
     ↓
OCR text + confidence + bounding boxes
     ↓
Section / region detection
     ↓
Semantic extraction
 ┌──────────────┬──────────────┬──────────────┐
 │ Product      │ Food label   │ Compliance   │
 │ identity     │ analysis     │ declarations │
 └──────────────┴──────────────┴──────────────┘
     ↓
Evidence-aware validation
     ↓
Product + scan persistence
     ↓
FastAPI JSON API
     ↓
NIVAR web interface
```

Current analysis areas include product name/brand, manufacturer/packer/importer, net quantity, manufacture/packing date, MRP, consumer-care details, conditional country-of-origin handling, ingredients, allergens, nutrition, OCR evidence, multi-image fusion, product history and image quality.

## Compliance semantics

NIVAR deliberately separates **detection** from **legal compliance**.

- **FOUND** — supporting evidence for the declaration was detected.
- **REVIEW** — an indication was detected, but evidence is insufficient for a confident automated conclusion.
- **NOT_FOUND** — the expected declaration was not detected in the searchable OCR/evidence set.

A `NOT_FOUND` result does not prove that a declaration is physically absent. OCR can miss text because of blur, glare, orientation, layout, occlusion or other image conditions.

Likewise, `FOUND` does not mean that the declaration has been legally certified as correct.

The overall validator can produce `COMPLIANT`, `REVIEW`, or `NON_COMPLIANT` according to the current supported checks.

## Product identity

Product identity is kept separate from manufacturer and address extraction.

The current strategy prioritizes:

1. Explicit labels such as **Product Name**, **Name of Product**, or **Name of Food**
2. Plausible front-panel product candidates
3. Nearby OCR text that can form a product-name candidate
4. Ordered OCR fallback

Candidates resembling company names, addresses, ingredients, nutrition text, compliance declarations or marketing copy are rejected or penalized.

```text
Brand
Product / commodity name
Manufacturer / packer / importer
Manufacturer address
Marketing copy
```

## OCR architecture

PaddleOCR is the primary OCR implementation. OCR observations preserve recognized text, confidence, bounding boxes and source-image context.

The provider-oriented design also retains Tesseract support for compatible workflows.

Configured OCR language codes:

```text
en, hi, mr, te, ta, ka, sa, bho, mai, gom, bgc
```

## Multi-image analysis

A product scan can contain **up to 8 images**.

```text
Front / back / side / close-up images
              ↓
       per-image analysis
              ↓
        evidence fusion
              ↓
       product-level result
```

Persisted image records retain image-level provenance so evidence can be traced back to a source image.

## Persistence

NIVAR currently uses a lightweight JSON-backed product repository.

It models:

- Product
- Scan
- Image
- Analysis snapshot
- Compliance result
- OCR summary

Each product can have multiple scans and each scan can contain multiple images. Uploaded scan images are copied into product-specific storage so history can be reconstructed without rerunning OCR.

The repository is intentionally lightweight at this stage and can later be replaced by database-backed persistence.

## Web application

The frontend is a **React + TypeScript + Vite** application.

Current flow:

```text
Home → Upload → Processing → Results → History
```

The Processing page provides an image-first scan experience. Results exposes structured product, food-label and compliance information. History reads persisted product/scan data.

## REST API

### Health

```http
GET /health
```

### Analyze product

```http
POST /api/v1/analyze
POST /api/v1/products/analyze
```

The endpoints accept multipart `images` plus an optional `language` field.

Current limits:

- Maximum 8 images per scan
- Maximum 15 MB per image
- JPG/JPEG/PNG/WEBP

### Stored scan image

```http
GET /api/v1/products/{product_id}/scans/{scan_id}/images/{image_id}
```

See [docs/api.md](docs/api.md) for the current API contract.

## Technology stack

| Layer | Technology |
|---|---|
| Backend | Python |
| API | FastAPI |
| Computer vision | OpenCV |
| Primary OCR | PaddleOCR 3.7.0 |
| OCR runtime | PaddlePaddle 3.2.2 |
| Secondary OCR | Tesseract |
| Data processing | Pandas |
| Frontend | React + TypeScript + Vite |
| Persistence | JSON-backed repository |
| Testing | Pytest |
| CI | GitHub Actions |
| Packaging | Docker |

The PaddleOCR/PaddlePaddle versions are intentionally frozen while extraction behavior is being stabilized.

## Repository structure

```text
NIVAR/
├── app/                         # FastAPI and application services
├── src/
│   ├── compliance/              # Declaration extraction + validation
│   ├── food_analysis/            # Nutrition, ingredients, allergens
│   ├── image_quality/            # Image quality checks
│   ├── ocr/                      # OCR, preprocessing, regions
│   ├── product_intelligence/     # Identity + evidence fusion
│   ├── repository/               # Product/scan persistence
│   └── reporting/                # JSON/debug reporting
├── frontend/                     # React/Vite client
├── tests/                        # Regression and unit tests
├── docs/                         # Architecture, API and roadmap
├── requirements.txt
├── Dockerfile
└── README.md
```

## Installation

### Backend

```bash
git clone https://github.com/tanmayjain9059/NIVAR.git
cd NIVAR
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For the current OCR stack:

```text
paddleocr==3.7.0
paddlepaddle==3.2.2
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

The Vite development server proxies `/api` and `/health` to FastAPI.

### Run FastAPI

From the repository root:

```bash
source venv/bin/activate
uvicorn app.api:app --reload
```

For direct analyzer/debug execution:

```bash
python -m app.main <image-path>
```

## Testing

Backend regression suite:

```bash
pytest -q tests/test_extraction_regressions.py
```

Full test suite:

```bash
pytest -q
```

Frontend build:

```bash
cd frontend
npm run build
```

GitHub Actions validates the backend regression suite and frontend build through `.github/workflows/validation.yml`.

## Docker

The repository contains a multi-stage Docker build.

On Apple Silicon, use an explicit deployment platform when required by the target environment:

```bash
docker build --platform linux/amd64 -t nivar .
```

## Evidence model

A core NIVAR principle is:

> **Do not make an automated conclusion without preserving the evidence that supports it.**

Evidence can contain:

```json
{
  "text": "MRP ₹142.00",
  "confidence": 0.99,
  "bbox": {
    "x1": 120,
    "y1": 300,
    "x2": 480,
    "y2": 360
  }
}
```

Evidence supports human review, frontend highlighting, debugging, regression tests and future placement/readability checks.

## Current development status

### Implemented

- [x] PaddleOCR integration
- [x] OCR confidence and bounding boxes
- [x] Image quality assessment
- [x] Section/region detection
- [x] Nutrition extraction
- [x] Section-scoped ingredient extraction
- [x] Conservative allergen extraction
- [x] Product identity extraction
- [x] Multi-image evidence fusion
- [x] Legal Metrology declaration extraction
- [x] Evidence-aware validation
- [x] Product/scan/image repository
- [x] Permanent scan-image storage
- [x] FastAPI analysis API
- [x] React/Vite frontend
- [x] Scan history UI
- [x] Regression tests
- [x] GitHub Actions validation

### In development

- [ ] Stronger mandatory-value extraction across varied label layouts
- [ ] More representative compliance fixtures
- [ ] Evidence visualization on source images
- [ ] Improved product identity coverage
- [ ] Expanded conditional-rule handling

### Planned

- [ ] Font-size verification
- [ ] Placement verification
- [ ] More complete correctness checks
- [ ] Database-backed persistence
- [ ] Production deployment
- [ ] Authentication / reviewer workflows

## Known limitations

NIVAR is not yet a complete automated legal-verification platform.

- OCR can fail on difficult images.
- Detection does not prove physical absence.
- Text presence is not equivalent to legal correctness.
- Font-size verification is not fully implemented.
- Full placement verification is not fully implemented.
- Some conditional declarations require product context.
- The JSON repository has scaling/concurrency limitations.
- Regulatory decisions should include appropriate human verification.

## Development principles

1. Evidence before assumptions.
2. Detection is not certification.
3. Preserve OCR geometry.
4. Keep product identity separate from manufacturer identity.
5. Prefer deterministic, testable rules over opaque guesses.
6. Use human review when evidence is insufficient.
7. Keep frontend, API, analysis and persistence boundaries clear.
8. Add regression tests when extraction behavior changes.

## Documentation

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Development roadmap](docs/TODO.md)
- [Project context](docs/CODEX_CONTEXT.md)

## License

The project is currently under development for Smart India Hackathon 2026. Licensing will be finalized by the project team.
