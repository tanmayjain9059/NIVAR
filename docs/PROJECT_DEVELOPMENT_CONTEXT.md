# NIVAR — Complete Project Development Context

Project: NIVAR
Repository: tanmayjain9059/NIVAR
Primary development branch: semantic-extraction-rewrite
SIH Problem Statement: SIH26034
Problem: Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.
Context updated: 2026-09-23

This is the long-form historical context for continuing NIVAR development in another chat/model. It reconstructs the project journey from the initial concept through the current semantic-extraction phase using project history, repository checkpoints, source structure, tests, and prior development discussions. Current source code and tests are authoritative.

---

## 1. Executive project history

NIVAR started as an SIH-focused idea for automatically checking packaged-commodity labels for Legal Metrology compliance.

The original concept was:

Product image -> OCR -> identify mandatory declarations -> validate -> show result.

The project evolved into an evidence-aware analysis platform.

The system progressively gained:

- image quality assessment;
- OpenCV preprocessing;
- Tesseract OCR experiments;
- PaddleOCR integration;
- OCR bounding boxes and confidence;
- automatic label-region detection;
- nutrition extraction;
- ingredients extraction;
- allergen extraction;
- product identity extraction;
- Legal Metrology declaration extraction;
- evidence-aware validation;
- multi-image evidence fusion;
- persistent products/scans/source images;
- FastAPI;
- React/Vite frontend;
- History and Results UI;
- regression tests;
- GitHub Actions;
- deployment preparation;
- semantic extraction rewrite.

The most important discovery is that OCR recognition and compliance extraction are different problems. Text can be visibly present on a package while NIVAR still returns NOT_FOUND because the system failed to associate that OCR text with the required declaration.

That extraction/evidence-association problem is now the main engineering priority.

---

# 2. Batch 0 — SIH problem framing

## Goal

Build a practical system for SIH26034 that scans packaged commodities and checks whether required declarations are present.

Core declarations identified:

1. Manufacturer / packer / importer name and address
2. Net quantity
3. Manufacture / packing / import date information
4. Maximum Retail Price (MRP)
5. Consumer-care details

Additional/conditional concepts:

- country of origin;
- generic/common name;
- food-label information such as ingredients, allergens and nutrition.

The system was deliberately framed as an automated screening/decision-support tool, not a legal certification system.

The SIH presentation work also established the need for:

- a clear problem statement;
- solution and innovation;
- justified technology choices;
- simple architecture;
- feasibility;
- risks and mitigation;
- impact;
- scalability;
- research/reference support;
- a coherent problem -> solution -> MVP story.

---

# 3. Batch 1 — Initial OpenCV + Tesseract prototype

The first prototype used:

- Python
- OpenCV
- Pillow
- Tesseract
- pytesseract
- Tkinter

Development was done locally on macOS, including a project path similar to /Users/tillu/Projects/opencv-label-analyzer.

Experiments included:

- resizing;
- grayscale conversion;
- adaptive thresholding;
- sharpening;
- OCR text extraction;
- OCR bounding boxes;
- displaying green OCR boxes.

Tesseract successfully extracted substantial packaging text, including nutrition headings, ingredients, consumer-care information and marketing text.

This established the first major architectural lesson:

OCR must preserve geometry and confidence, not only return a text string.

Problems discovered:

- blur;
- low contrast;
- mixed font sizes;
- curved packaging;
- rotated text;
- OCR noise;
- marketing text mixed with declarations;
- inability to know which text belonged to which package section.

Therefore whole-image OCR alone was insufficient.

---

# 4. Batch 2 — Automatic section and ROI analysis

A script called automatic_analyzer.py was developed to automatically identify useful label sections.

Target sections included:

- Ingredients
- Nutrition
- Allergens

Observed automatic detections included examples such as:

Ingredients: x 2040, y 2017, w 563, h 93
Nutrition: x 387, y 2098, w 590, h 111
Allergens: x 2043, y 3088, w 364, h 120

The prototype could show detected regions and perform section OCR.

Important lesson:

Semantic extraction is much more reliable when the parser knows whether text belongs to nutrition, ingredients, allergens or compliance.

However, hard-coded image coordinates were rejected as a long-term solution.

The architecture moved toward:

OCR geometry -> heading/anchor detection -> logical region -> section OCR -> semantic extraction.

---

# 5. Batch 3 — PaddleOCR integration

Important repository checkpoints:

- eb8a615c3156e0333676f96504d66dd91c765be0 — Add PaddleOCR integration checkpoint
- 95686adab85527ed0906c898fbeefc1416d56857 — Checkpoint OCR and API integration

Current primary OCR:

- PaddleOCR 3.7.0
- PaddlePaddle 3.2.2

Tesseract remains available as a secondary OCR provider/workflow.

PaddleOCR configuration includes:

- document orientation classification;
- document unwarping;
- text-line orientation.

OCR output preserves:

- text;
- confidence;
- bounding box;
- language;
- original-image coordinate system.

Current language codes:

en, hi, mr, te, ta, ka, sa, bho, mai, gom, bgc.

The provider architecture was chosen so extraction logic would not be tightly coupled to one OCR library.

---

# 6. Batch 4 — Modular analyzer pipeline

Important checkpoints:

- 103ffcfb12bcd263bf0bfe41a63125b837e1dc1c — refactor: connect modular analyzer pipeline
- ac3fa8279047bed4a5a72d93ff4b2c3cb4a63460 — feat: working modular analyzer pipeline
- c52bbc51f1d4640e18e03b3d9b9f11687b75888c — refactor: extract food analysis and reporting

The project was reorganized into a modular pipeline:

Input image
-> image quality
-> preprocessing
-> OCR
-> region detection
-> section OCR
-> food analysis
-> compliance extraction
-> validation
-> structured result.

This separation became important because OCR, extraction, reporting and UI logic had previously become difficult to maintain when mixed together.

---

# 7. Batch 5 — Nutrition, ingredients and allergen analysis

Nutrition extraction became a combination of:

1. spatial OCR evidence;
2. text-based OCR evidence.

Spatial evidence is preferred and text extraction fills missing values.

A real large image, images/IMG_0980.jpeg, approximately 4110 x 5271, demonstrated strong nutrition extraction.

Observed values included:

- Energy: 513 kcal
- Protein: 11.53 g
- Carbohydrate: 56.9 g
- Total Sugars: 12.87 g
- Added Sugars: 11.58 g
- Dietary Fiber: 4.88 g
- Saturated Fat: 18.01 g
- Cholesterol: 61.37 mg
- Sodium: 693.54 mg
- Total Fat: 26.62 g
- Trans Fat: 0.68 g

This proved that the OCR/semantic pipeline could extract useful real-package data.

Ingredients became section-aware and should stop at later label sections.

Allergen extraction became conservative, looking for anchors such as Contains and May contain and filtering toward known allergen terminology.

Important rule:

Do not feed arbitrary global marketing text into ingredients/allergen parsers when a section-specific OCR result exists.

---

# 8. Batch 6 — Evidence-aware compliance

Checkpoint:

970cdb8824269c7093a7fca866f55b1e5eda521e — Add quality gating and evidence-based compliance

Core checks:

- manufacturer / packer / importer;
- net quantity;
- manufacture / packing date;
- MRP;
- consumer care.

Status model:

FOUND
REVIEW
NOT_FOUND

Interpretation:

FOUND means NIVAR detected suitable evidence. It is not legal certification.

REVIEW means evidence is ambiguous, incomplete or below the confidence requirement.

NOT_FOUND means NIVAR did not detect sufficient evidence. It does not prove the declaration is physically absent.

Image-quality gating was added so weak images do not produce unjustified confidence.

---

# 9. Batch 7 — PaddleOCR nutrition fixes and semantic extraction

Checkpoint:

27d44a1f10a0d5d42e077b83931aae71e06b26c4 — Fix PaddleOCR nutrition pipeline

The project moved increasingly toward semantic extraction rather than regex over the entire OCR text.

The conceptual model became:

OCR -> geometry -> logical regions -> semantic extraction -> validation.

This distinction is central to the current project.

---

# 10. Batch 8 — FastAPI backend

Checkpoints:

- 2971b7e97bf814881917aaf1cb475a014364b513 — checkpoint: stabilize backend before frontend integration
- df6885975206600931f19428ada640b22333c59b — feat: integrate NIVAR frontend with analyzer API

Current API routes:

GET /health
POST /api/v1/analyze
POST /api/v1/products/analyze
GET /api/v1/products/{product_id}/scans/{scan_id}/images/{image_id}

API constraints:

- JPG/JPEG/PNG/WEBP;
- maximum 8 images;
- maximum 15 MB per image.

The analyzer service accepts OCR language and invokes the modular analysis pipeline.

---

# 11. Batch 9 — React/Vite frontend

Technology:

- React
- TypeScript
- Vite

Main pages:

- Home
- Upload
- Processing
- Results
- History

Frontend responsibilities:

- image selection;
- multi-image upload;
- OCR language selection;
- processing visualization;
- structured results;
- compliance status;
- evidence/source images;
- scan history.

The UI was designed for both real usage and SIH/demo presentation.

---

# 12. Batch 10 — Home and Upload UI optimization

Checkpoint:

e4bbb1166e783917fbc47b3d0687a4327e6102ae — checkpoint: optimized home and upload UI

The application was organized into a clear:

Home -> Upload -> Processing -> Results -> History

experience.

The project began focusing not only on backend correctness but also on making the workflow understandable to a jury/user.

---

# 13. Batch 11 — Compliance Results and UI

Checkpoint:

19228d5f39db87e400e19ee4582ffc1276b41d94 — checkpoint: compliance analysis and UI updates

Results were expanded to expose actual structured analysis.

The desired evidence model became:

Requirement
-> status
-> detected value
-> matched text
-> confidence
-> source evidence.

This evidence-first UI remains a core NIVAR principle.

---

# 14. Batch 12 — Product repository and persistence

Checkpoint:

5a613ccf9f2ae7108f8cf27c1529f2b916d30db3 — Add product repository foundation

Current conceptual model:

ProductRecord
  -> ScanRecord[]
      -> ImageRecord[]

Current development persistence is JSON-backed.

Uploaded images are copied into product-specific storage.

The complete analysis snapshot is retained.

This enables:

- product history;
- scan history;
- source-image retrieval;
- provenance;
- evidence inspection.

This is suitable for the current development stage but not the final production database architecture.

---

# 15. Batch 13 — MVP deployment

Checkpoints:

- 52ad04c1ba67777fc96bcd56ec111f9338c5c6ea — release: NIVAR MVP deployment checkpoint
- 245f05af500f39d1cf206033f2aec90fed1439d0 — deploy: prepare NIVAR backend for hosting

The system became a genuine end-to-end MVP.

Deployment architecture:

React/Vite build
-> FastAPI
-> analyzer service
-> OCR/extraction
-> persistence.

FastAPI can serve frontend/dist when the frontend build exists.

Docker deployment was prepared using a multi-stage frontend/backend build.

---

# 16. Batch 14 — Regression testing

Checkpoint:

63b33a35267361daf0c940ec951bfc22e51f07a7 — test: add product intelligence regression suite

Testing expanded to cover:

- extraction regressions;
- multi-image fusion;
- product identity;
- repository;
- semantic extraction;
- conflict handling.

Important development rule established:

Every important extraction behavior should have regression coverage.

---

# 17. Batch 15 — Semantic extraction rewrite

This is the current major phase.

The rewrite was motivated by real-image behavior: OCR could read substantial text but semantic extraction could still map the wrong text to the wrong field.

## Product identity

The previous product-identity implementation became too complicated and over-optimized.

It was simplified to:

1. explicit Product Name / Name of Product / Name of Food;
2. plausible front-panel candidates;
3. nearby OCR-token joins;
4. ordered global OCR fallback.

Candidates resembling the following are rejected or penalized:

- company names;
- addresses;
- nutrition;
- ingredients;
- compliance declarations;
- marketing copy.

Product identity must remain separate from:

- brand;
- manufacturer;
- manufacturer address;
- marketing copy.

---

# 18. Manufacturer extraction correction

A real bug was discovered where address text was selected as the manufacturer.

The implementation was changed to score manufacturer/entity candidates using company/legal-entity signals while penalizing:

- address indicators;
- phone numbers;
- emails;
- PIN codes.

Manufacturer name and manufacturer address are stored separately.

If address evidence is missing, the compliance result can remain REVIEW rather than falsely claiming a complete manufacturer declaration.

This was captured in:

31810fcb1fcd02397af33c8d79f413a540d7649e — fix: select manufacturer entity instead of address text

---

# 19. Real-image testing and the key discovery

The image images/IMG_0980.jpeg produced a large amount of OCR text and strong nutrition extraction.

However, the five core Legal Metrology declarations were not reliably detected.

Observed behavior included:

Manufacturer/Packer/Importer -> NOT_FOUND
Net Quantity -> NOT_FOUND
Manufacture Date -> NOT_FOUND
MRP -> NOT_FOUND
Consumer Care -> NOT_FOUND

This led to the current central problem:

The package can visibly contain the declarations while NIVAR reports NOT_FOUND.

This means the problem cannot be treated simply as “OCR is bad.”

The failure can occur at five layers:

1. text detection;
2. text recognition;
3. region association;
4. semantic interpretation;
5. compliance validation.

---

# 20. Current critical problem — declaration extraction

The most important current task is improving detection of the five declarations:

1. Manufacturer / packer / importer
2. Net quantity
3. Manufacture / packing / import date
4. MRP
5. Consumer care

The recommended approach is not to immediately replace PaddleOCR.

Instead, strengthen the semantic extraction layer.

## Anchor detection

Recognize label variations such as:

- MRP
- M.R.P.
- Maximum Retail Price
- Net Quantity
- Net Qty
- Manufactured
- Manufactured by
- Packed
- Packed by
- Imported by
- Mfg
- Mfg.
- Pkd
- Pkd.
- Customer Care
- Consumer Care

## OCR normalization

Normalize common OCR variations such as:

M.R.P -> MRP
M R P -> MRP
MRP. -> MRP
Mfg. -> Mfg
Pkd. -> Pkd

Normalization should happen before matching.

## Spatial association

Once an anchor is found, search nearby OCR lines instead of searching the entire OCR string.

For example:

MRP anchor
-> same line / next lines
-> currency candidate
-> numeric candidate
-> evidence.

## Multi-line grouping

Manufacturer declarations may span multiple lines:

Manufactured by:
ABC Foods Pvt Ltd
Plot 12, Industrial Area
Hyderabad - 500001

The extractor must group those lines into one declaration evidence object.

## Typed candidate validation

Expected value types matter.

Examples:

- MRP -> currency/price;
- net quantity -> quantity + unit;
- manufacture date -> date/month/year;
- consumer care -> phone/email/address;
- manufacturer -> legal entity + address.

This avoids confusing arbitrary numbers with declarations.

## Candidate scoring

Candidate score should consider:

- anchor strength;
- spatial distance;
- same-line relationship;
- expected value type;
- OCR confidence;
- neighboring lines;
- region context;
- image/source.

## Cross-image evidence fusion

If one image contains the declaration label and another image contains the associated value, evidence fusion should combine them when context supports the relationship.

---

# 21. Current OCR implementation

Current src/ocr/paddle_engine.py:

- caches PaddleOCR models by language;
- resizes very large images;
- preserves original coordinate scaling;
- extracts OCR lines;
- preserves confidence;
- preserves bounding boxes;
- reports original-image coordinates.

Current default maximum OCR side is 3200 pixels.

PaddleOCR currently has orientation/unwarping support.

This gives NIVAR a foundation for curved/distorted packaging, but it does not guarantee reliable OCR on cylindrical labels.

---

# 22. Planned curves, bends and cylindrical-surface enhancement

A later computer-vision stage should target:

- bottles;
- jars;
- cans;
- cylindrical containers;
- curved labels;
- bent pouches;
- perspective-heavy photographs.

Target architecture:

Input image
-> distortion/surface assessment
-> choose processing strategy
-> original or unwarped or cylindrical-unwrapped representation
-> OCR
-> compare evidence quality
-> use strongest representation.

Do not send every image through expensive cylindrical processing.

Keep existing PaddleOCR unwarping and add cylindrical processing as a conditional fallback/multi-pass strategy.

This should be done after baseline declaration extraction is reliable.

---

# 23. Frontend repeated-scanner issue

The Processing UI was redesigned to include:

- large product image;
- animated scanner sweep;
- LIVE SCAN;
- PaddleOCR + NIVAR indicator;
- thumbnail strip;
- progress;
- analysis pipeline steps;
- error state.

Checkpoint:

2329761588565cd8dd8286f9fa00a39b70f11922 — ui: restore large product scanner loading experience

A real user-reported issue was:

“The new scanner UI worked only once, then the old UI appeared for other scans.”

This must be treated as a real frontend lifecycle/build/runtime issue.

The source currently has a Processing page and App renders Processing during the PROCESSING state, but a direct browser-level repeated-scan test has not been conclusively completed in this project context.

Do not claim this is fixed until it is actually reproduced and tested.

---

# 24. CI history and lessons

GitHub Actions workflow:

.github/workflows/validation.yml

Backend:

pytest -q tests/test_extraction_regressions.py

Frontend:

npm ci
npm run build

Recent CI failures exposed malformed string literals in src/ocr/engine.py.

Two different newline-join syntax issues were found during development.

Fixes included:

- befbf213f5feac604b069f9c56152756000ab0e4 — fix: repair Paddle OCR text join syntax
- e06cf8cd82848551c2ada1254b24b9c972fbdc91 — fix: repair remaining OCR region join syntax

Important lesson:

Never declare CI green from source inspection alone. Always inspect the current workflow result.

---

# 25. Current source architecture

Backend:

app/main.py
app/api.py
app/services/analyzer_service.py
app/services/product_service.py

OCR:

src/ocr/engine.py
src/ocr/paddle_engine.py
src/ocr/provider.py
src/ocr/preprocessing.py

Compliance:

src/compliance/enhanced_extractor.py
src/compliance/validator.py
src/compliance/rules.py

Food analysis:

src/food_analysis/nutrition.py
src/food_analysis/ingredients.py
src/food_analysis/allergens.py

Product intelligence:

src/product_intelligence/identity.py
src/product_intelligence/fusion.py

Repository:

src/repository/models.py
src/repository/store.py

Frontend:

frontend/src/App.tsx
frontend/src/pages/Home
frontend/src/pages/Upload
frontend/src/pages/Processing
frontend/src/pages/Results
frontend/src/pages/History

Tests:

tests/test_extraction_regressions.py
tests/test_fusion_conflicts.py
tests/test_product_fusion.py
tests/test_product_identity.py
tests/test_repository.py
tests/test_semantic_extraction.py

---

# 26. Current technology stack

Backend:

- Python
- FastAPI
- Uvicorn
- Pydantic

Computer vision:

- OpenCV
- Pillow

OCR:

- PaddleOCR 3.7.0
- PaddlePaddle 3.2.2
- Tesseract / pytesseract

Data processing:

- pandas
- NumPy

Frontend:

- React
- TypeScript
- Vite

Persistence:

- JSON-backed development repository
- local image storage

---

# 27. Important engineering principles learned

1. Preserve OCR evidence.
2. Preserve bounding boxes and confidence.
3. Separate OCR from semantic extraction.
4. Separate semantic extraction from compliance validation.
5. Do not infer missing declarations from unrelated numbers.
6. Use spatial relationships.
7. Do not hard-code coordinates.
8. Keep product, brand, manufacturer and address separate.
9. Use REVIEW for ambiguity.
10. NOT_FOUND means not detected, not physically absent.
11. Multi-image scans are evidence fusion.
12. Test real package images.
13. Add regression tests for important extraction behavior.
14. Verify CI before declaring a change complete.
15. Keep legal rules in the compliance layer.
16. Keep API concerns out of OCR/extraction modules.

---

# 28. What is already proven to work

NIVAR has successfully established:

- PaddleOCR integration;
- multilingual OCR configuration;
- OCR geometry preservation;
- image-quality gating;
- nutrition extraction on real packaging;
- ingredients extraction framework;
- allergen extraction framework;
- product identity extraction hierarchy;
- compliance extraction framework;
- evidence-aware validation;
- multi-image analysis;
- evidence fusion;
- product/scan/image persistence;
- FastAPI API;
- React/Vite frontend;
- source-image serving;
- regression testing;
- frontend build validation;
- deployment preparation.

Therefore the project is no longer a from-scratch prototype.

The primary engineering challenge is now extraction reliability on real packaging.

---

# 29. Current priority order

Priority 1 — Fix the five-declaration extraction.

Implement:

- OCR normalization;
- declaration anchors;
- spatial neighborhoods;
- line grouping;
- typed candidates;
- confidence scoring;
- evidence objects;
- cross-image fusion.

Priority 2 — Build a declaration evidence visualizer.

For every declaration show:

Requirement
-> detected anchor
-> matched value
-> bounding box
-> confidence
-> source image.

Priority 3 — Improve curved/cylindrical packaging.

Use:

- existing PaddleOCR unwarping;
- distortion detection;
- cylindrical unwrap fallback;
- OCR on transformed representations;
- best-evidence selection.

Priority 4 — Reproduce and fix repeated scanner UI behavior.

Test:

Scan A -> Processing -> Results -> Scan again -> Processing -> Results -> Scan again.

Priority 5 — Deployment validation.

Test:

- clean container;
- API;
- frontend;
- OCR models;
- persistent storage;
- multi-image scans;
- real product images.

---

# 30. Recommended declaration-extraction architecture

The next compliance extractor should conceptually be:

OCR lines
-> normalize text
-> detect declaration anchors
-> group nearby lines
-> generate typed candidates
-> score candidates
-> attach evidence
-> fuse evidence across images
-> validate.

Example MRP:

OCR lines:
“M.R.P.”
“₹”
“120.00”
“incl. all taxes”

Anchor:
MRP

Candidate window:
same line + nearby lines

Expected type:
currency

Evidence:
anchor + proximity + currency + numeric pattern + OCR confidence

Result:
FOUND

Example manufacturer:

Anchor:
Manufactured by

Candidate group:
ABC Foods Pvt Ltd
Plot 12, Industrial Area
Hyderabad - 500001

Entity:
ABC Foods Pvt Ltd

Address:
Plot 12...
Hyderabad...

Result:
FOUND only when the required entity/address evidence is sufficiently supported.

---

# 31. Real-world testing dataset needed

Future tests should include:

Flat packages:
- boxes;
- cartons;
- flat pouches.

Curved:
- bottles;
- jars;
- cans.

Distorted:
- folded pouches;
- crumpled wrappers;
- perspective-heavy photographs.

Text conditions:
- tiny MRP;
- low contrast;
- embossed text;
- multilingual text;
- rotated text;
- split lines.

Declaration placement:
- back panel;
- side panel;
- bottom edge;
- near barcode;
- around nutrition table;
- near consumer-care block.

The success metric should not be OCR accuracy alone.

The critical metric is:

Correct declaration-to-value association.

---

# 32. Current mental model

NIVAR should now be understood as five layers:

Layer 1 — Vision
Find text and package regions.

Layer 2 — OCR
Read text and preserve geometry/confidence.

Layer 3 — Semantic extraction
Understand what each piece of text means.

Layer 4 — Compliance
Compare evidence against configured requirements.

Layer 5 — Evidence/UI
Explain why the system reached its result.

The current weakness is primarily between Layers 2 and 4:

OCR text exists
-> meaning is not reliably associated
-> compliance becomes NOT_FOUND or REVIEW.

---

# 33. Important recent commits

2329761588565cd8dd8286f9fa00a39b70f11922
ui: restore large product scanner loading experience

31810fcb1fcd02397af33c8d79f413a540d7649e
fix: select manufacturer entity instead of address text

b8e321252da06b7df0d091ccf2a8c67cb960db04
refactor: simplify product identity extraction

befbf213f5feac604b069f9c56152756000ab0e4
fix: repair Paddle OCR text join syntax

d0103afbeff700ca04e12ab1f67b906568780a04
docs: refresh NIVAR README

03a2a1cee30af60661d9361e4414f3377fe61d16
docs: document NIVAR architecture

de15c7b330cc2e7c94520d0d3fc375f049f9f4fa
docs: document NIVAR API

a946a9842f51ec8b38de57f1b7038e09dd8ed843
docs: refresh NIVAR roadmap

d56448c6cf43a0eaf92456a8921cc35dc0c9818e
docs: refresh current project context

e06cf8cd82848551c2ada1254b24b9c972fbdc91
fix: repair remaining OCR region join syntax

---

# 34. Continuation brief for another model

NIVAR is an existing end-to-end packaged-commodity compliance system. Do not restart the architecture.

Do not replace PaddleOCR simply because compliance fields are missing.

Do not treat OCR text extraction as semantic extraction.

The immediate problem is:

Five mandatory Legal Metrology declarations can be visibly present in a product image while NIVAR returns NOT_FOUND.

The next engineering task is to inspect the current compliance extractor and strengthen declaration evidence association using:

- anchors;
- OCR normalization;
- spatial neighborhoods;
- multi-line grouping;
- typed value candidates;
- confidence scoring;
- multi-image fusion;
- evidence visualization.

Only after baseline declaration extraction becomes reliable should advanced curved/cylindrical surface handling be implemented.

Target end state:

REAL PRODUCT IMAGE
-> QUALITY / DISTORTION ANALYSIS
-> OCR + GEOMETRY
-> DECLARATION ANCHORS
-> SPATIAL EVIDENCE GROUPING
-> SEMANTIC VALUE EXTRACTION
-> CROSS-IMAGE FUSION
-> LEGAL-METROLOGY VALIDATION
-> FOUND / REVIEW / NOT_FOUND
-> VISUAL EVIDENCE

This evidence-first pipeline is the central direction for the next phase of NIVAR.
