# NIVAR Development Roadmap

This is the working roadmap for the current `semantic-extraction-rewrite` development line.

Source code and regression tests are authoritative. A checked item means the capability exists in the current branch; it does not mean the feature is legally complete or production-certified.

## P0 — Foundation

- [x] PaddleOCR primary pipeline
- [x] OCR confidence and bounding-box preservation
- [x] Image quality assessment
- [x] Section/region detection
- [x] Nutrition extraction
- [x] Section-scoped ingredient extraction
- [x] Conservative allergen extraction
- [x] Product identity extraction
- [x] Multi-image evidence fusion
- [x] Legal Metrology declaration extraction
- [x] Evidence-aware compliance validation
- [x] Product/scan/image repository
- [x] Permanent scan-image storage
- [x] FastAPI analysis boundary
- [x] React/Vite frontend
- [x] Scan history UI
- [x] Regression tests
- [x] GitHub Actions backend/frontend validation

## P1 — Extraction reliability

- [ ] Expand representative real-label regression fixtures.
- [ ] Improve separated declaration/value association for varied layouts.
- [ ] Improve net-quantity and MRP extraction without accepting unrelated numbers.
- [ ] Improve manufacture/packing-date extraction across label formats.
- [ ] Continue product-name extraction using explicit label evidence first.
- [ ] Improve manufacturer entity/address separation.
- [ ] Preserve evidence provenance through every new extraction path.
- [ ] Keep `FOUND / REVIEW / NOT_FOUND` semantics stable unless a regression test justifies a change.

## P2 — Compliance depth

- [ ] Audit supported declarations against applicable SIH26034 requirements and project references.
- [ ] Improve conditional country-of-origin applicability handling.
- [ ] Define defensible generic/common-name handling.
- [ ] Add bounded correctness checks where inputs and evidence are sufficient.
- [ ] Add placement verification when legal/layout criteria and image calibration are defined.
- [ ] Investigate font-size/readability verification with calibrated image evidence.
- [ ] Document every automated rule's evidence and manual-review boundary.

## P3 — Evidence and UX

- [ ] Highlight declaration evidence on source images.
- [ ] Show image-specific provenance in Results.
- [ ] Surface OCR confidence and review reasons clearly.
- [ ] Improve multi-image result comparison.
- [ ] Generate downloadable compliance/evidence reports.
- [ ] Improve History filtering and scan comparison.

## P4 — Persistence and deployment

- [ ] Audit JSON repository limits for concurrent/production use.
- [ ] Introduce database-backed persistence when required.
- [ ] Add authentication and role-based access if required.
- [ ] Add deployment configuration.
- [ ] Add observability/logging suitable for hosted operation.
- [ ] Define retention and data-management policy for uploaded package images.

## P5 — Platform expansion

- [ ] Android integration
- [ ] Web dashboard expansion
- [ ] Reviewer workflow
- [ ] Product compliance history
- [ ] Enforcement/reporting workflow

## Non-goals for the current phase

Do not:

- treat OCR presence as legal certification;
- infer missing values from unrelated numbers;
- add repeated full-image OCR without measured need;
- optimize aggregate compliance counts without evidence;
- hard-code image-specific coordinates;
- claim a rule is implemented merely because a placeholder field exists.

## Verification rule

For an extraction change:

```text
Implement
   ↓
Add regression fixture
   ↓
Run targeted tests
   ↓
Run full test suite
   ↓
Run frontend build when relevant
   ↓
Verify CI
   ↓
Update documentation
```
