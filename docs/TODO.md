# SIH26034 Backend TODO

This is the ordered execution queue. `AGENTS.md` defines working rules, `docs/CODEX_CONTEXT.md` records current technical facts, and active source code is authoritative. Work one task at a time, in order: inspect → smallest change → compile → test → verify → update context/TODO → stop. Do not treat this document as evidence that a listed feature exists.

## P0 — Current Critical Foundation

- [x] Persist compact OCR summary in `ScanRecord`.
  - Purpose: expose a small, serializable OCR summary with `engine`, `line_count`, and `average_confidence` for each product scan.
  - Affected: `app/main.py`, `src/ocr/engine.py`, `src/reporting/json_report.py`, `app/api.py`, `app/services/product_service.py`, `src/repository/models.py`.
  - Dependency: preserve one global PaddleOCR inference and the current pandas DataFrame.
  - Verify: completed successfully. A real product analysis produced `{"engine": "paddle", "line_count": 102, "average_confidence": 0.9743}` and persisted it in the scan record.

- [x] Verify OCR persistence through the individual scan-detail API.
  - Purpose: prove the persisted summary is returned by `GET /api/v1/products/{product_id}/scans/{scan_id}`.
  - Affected: `app/api.py`, `app/services/product_service.py`, `src/repository/store.py`, `data/`.
  - Dependency: completed compact OCR summary persistence.
  - Verify: manually analyzed product `PROD-CEDA8D643438` with scan `SCAN-E69346941835`; the POST response and subsequent scan-detail GET returned the identical OCR summary:
    - `engine`: `paddle`
    - `line_count`: `102`
    - `average_confidence`: `0.9743`
  - Additional verification: `image_quality` and `compliance` were persisted, and the permanent scan image exists at `data/product_images/PROD-CEDA8D643438/SCAN-E69346941835.jpg`.
  - Testing method: manual `curl` smoke testing; this is not an automated test.

- [ ] Create a clean Git checkpoint after OCR-persistence verification.
  - Purpose: preserve the verified backend-foundation state.
  - Affected: Git working tree only.
  - Dependency: completed OCR persistence verification and explicit user authorization to commit.
  - Verify: `git diff --check` is currently clean. The checkpoint remains open until the user explicitly authorizes a commit.

## P1 — Backend Reliability

- [ ] Repair `requirements.txt` with actual runtime dependencies.
  - Purpose: make a clean installation reproducible; the tracked file is currently empty.
  - Affected: `requirements.txt`.
  - Dependency: inventory active imports and choose compatible package versions.
  - Verify: a clean environment installs dependencies and imports the API successfully.

- [ ] Establish basic automated backend/API tests.
  - Purpose: replace manual-only curl smoke checking with a minimal repeatable test harness.
  - Affected: new test files, test configuration, `requirements.txt`.
  - Dependency: repaired requirements.
  - Verify: one documented test command discovers and runs the initial API tests.

- [ ] Add regression tests for product creation and scan history.
  - Purpose: protect product IDs, repository round-trips, and history ordering.
  - Affected: new tests for `app/api.py`, `app/services/product_service.py`, `src/repository/`.
  - Dependency: automated backend/API test harness.
  - Verify: tests create an isolated repository product and assert list/get/history results.

- [ ] Add a regression test for permanent image storage.
  - Purpose: protect copying to `data/product_images/<product_id>/<scan_id>.<extension>` and rollback behavior.
  - Affected: new tests for `app/services/product_service.py` and `src/repository/store.py`.
  - Dependency: automated test harness and isolated temporary test storage.
  - Verify: test asserts copied image existence and rollback removes only the failed copy.

- [ ] Add a regression test for image-quality rejection.
  - Purpose: protect the pre-OCR hard gate and its review-only result shape.
  - Affected: new tests for `app/main.py` and `src/image_quality/quality.py`.
  - Dependency: automated test harness.
  - Verify: a controlled failing image does not invoke OCR and returns the documented review result.

- [ ] Add a regression test for OCR-summary persistence.
  - Purpose: prevent `ScanRecord.ocr` from returning to null for new API scans.
  - Affected: new tests for the P0 flow.
  - Dependency: completed P0 OCR persistence and automated test harness.
  - Verify: test creates a scan and asserts its scan-detail response contains the expected summary.

## P2 — Compliance Accuracy

- [ ] Audit mandatory declaration extraction against SIH26034 requirements.
  - Purpose: compare implemented rules with the applicable project objective without claiming legal certification.
  - Affected: `src/compliance/rules.py`, `extractor.py`, `validator.py`, documentation.
  - Dependency: representative labels and authoritative rule interpretation.
  - Verify: a documented gap matrix separates implemented, review-only, and unsupported checks.

- [ ] Implement spatial declaration-value association for separated labels and values.
  - Purpose: associate PKD/MFD/MFG/MRP anchors with plausible separately OCR-recognized date or price values in adjacent-line, whitespace-separated, horizontal, vertical, or boxed/rectangular label layouts.
  - Affected: `src/compliance/extractor.py`, `src/compliance/validator.py`, `src/ocr/regions.py`, and a small dedicated spatial-association helper only if that keeps responsibilities clearer.
  - Dependency: existing OCR DataFrame bounding boxes and confidence values; representative packaged-label rectangle-layout evidence.
  - Verify: anchors are detected with separate nearby values; geometry selects horizontal and vertical candidates without unrelated-number associations; returned evidence preserves text, confidence, and bounding boxes; no additional PaddleOCR inference occurs; existing compliance cases do not regress. Implement rectangle detection only if OCR geometry alone proves insufficient for representative images.

- [ ] Improve mandatory declaration value extraction.
  - Purpose: improve deterministic extraction of values required by currently supported labels, such as net quantity and MRP.
  - Affected: `src/compliance/extractor.py`, tests.
  - Dependency: audited failure examples.
  - Verify: new fixtures show correct value detection without accepting unrelated numeric text.

- [ ] Reduce avoidable `REVIEW` results using deterministic evidence.
  - Purpose: improve evidence extraction only where reliable rules can support it.
  - Affected: `src/compliance/extractor.py`, `validator.py`, tests.
  - Dependency: mandatory-value extraction and labeled failure cases.
  - Verify: targeted cases move to `FOUND` only with supporting OCR evidence; do not optimize aggregate counts generally.

- [ ] Improve country-of-origin handling.
  - Purpose: separate detection from imported-product applicability.
  - Affected: `src/compliance/extractor.py`, `validator.py`, tests.
  - Dependency: defined deterministic applicability inputs.
  - Verify: absent origin remains `REVIEW` when applicability cannot be established.

- [ ] Improve generic/common-name detection.
  - Purpose: replace the current always-manual-review placeholder only with defensible extraction rules.
  - Affected: `src/compliance/extractor.py`, `validator.py`, tests.
  - Dependency: representative labels and a defined common-name rule.
  - Verify: unsupported cases still remain `REVIEW` and no legal claim is produced.

- [ ] Implement correctness checks where technically supportable.
  - Purpose: add bounded deterministic checks after requirements audit.
  - Affected: compliance modules and tests.
  - Dependency: authoritative rule interpretation and evidence semantics.
  - Verify: each new check has a documented input, evidence rule, and manual-review fallback.

- [ ] Implement placement checks.
  - Purpose: use existing bounding boxes only when image/layout criteria are defined.
  - Affected: `src/compliance/`, possibly `src/ocr/regions.py`, tests.
  - Dependency: legal placement criteria and calibrated image geometry.
  - Verify: test images demonstrate reliable placement outcomes; otherwise retain `REVIEW`.

- [ ] Investigate font-size/readability verification.
  - Purpose: determine whether scale calibration and image quality support defensible checks.
  - Affected: documentation, possible future CV/compliance modules.
  - Dependency: calibrated images and rule criteria.
  - Verify: decision record shows implementable method or explains why it remains deferred.

- [ ] Improve conditional-rule handling.
  - Purpose: model when conditional declarations apply without using barcode as evidence.
  - Affected: `src/compliance/`, product metadata contract, tests.
  - Dependency: explicit product-context inputs.
  - Verify: conditional results explain applicability and preserve `REVIEW` when context is absent.

- [ ] Define evidence and report semantics for each compliance rule.
  - Purpose: make API/frontend interpretation consistent and reviewable.
  - Affected: compliance modules, API documentation, tests.
  - Dependency: mandatory-rule audit.
  - Verify: every check documents status meaning, evidence fields, and manual-review limits.

- [ ] Revisit `FOUND`/`REVIEW`/`NOT_FOUND` optimization.
  - Purpose: consider aggregate-status improvements only after backend foundation and evidence semantics are complete.
  - Affected: `src/compliance/validator.py`, tests, context.
  - Dependency: completion of P0/P1 and explicit user instruction.
  - Verify: no change is made without evidence-backed acceptance criteria and regression tests.
  - [ ] Implement targeted rotated declaration-value OCR recovery.
  - Purpose: recover declaration values that are visually present but missed by the global PaddleOCR pass, especially small values printed separately from declaration labels in rotated/boxed areas.
  - Confirmed test case: `ffd22a27-db93-4b9a-aede-7e428d1ba454.JPG`
  - Verified recovery:
    - Batch No. → `0301B17`
    - PKD. → `14/05/26`
    - Use By → `07/02/27`
    - MRP → `142.00`
  - Observed targeted OCR confidences: approximately 0.993–1.000.
  - Approach: trigger only when a declaration anchor is detected but its expected value is absent from global OCR; derive a constrained ROI from declaration geometry, apply the required rotation, and run targeted OCR.
  - Constraints:
    - do not run repeated full-image OCR;
    - do not hard-code image-specific coordinates;
    - preserve existing successful global-OCR extraction;
    - preserve confidence and bounding-box evidence;
    - do not associate unrelated numeric text;
    - add no second/third rotation attempt unless justified by test evidence.
  - Verification:
    - test across multiple images with separated declaration/value layouts;
    - test existing same-line cases for regression;
    - verify MRP, PKD/MFD, USE BY and batch recovery;
    - verify no unrelated numbers are selected.

## P3 — OCR / Vision Improvements

- [ ] Evaluate OCR confidence handling.
  - Purpose: determine whether stored confidence should affect extraction decisions or only evidence display.
  - Affected: `src/ocr/`, nutrition/compliance modules, tests.
  - Dependency: confidence-labeled failure cases.
  - Verify: decision is supported by measured examples; do not add thresholds speculatively.

- [ ] Evaluate difficult label layouts.
  - Purpose: measure region-detection behavior on varied packaging layouts.
  - Affected: `src/ocr/regions.py`, representative test assets, tests.
  - Dependency: representative image set.
  - Verify: documented failures and regression cases justify any heuristic change.

- [ ] Evaluate low-quality image behavior.
  - Purpose: calibrate the existing hard quality gate with real failure examples.
  - Affected: `src/image_quality/quality.py`, test assets, tests.
  - Dependency: representative low-quality images.
  - Verify: acceptance/rejection decisions are documented and regression-tested.

- [ ] Evaluate multilingual/Indian-language requirements if required by the problem statement.
  - Purpose: establish a requirement before changing OCR language configuration.
  - Affected: documentation, `src/ocr/paddle_engine.py` only if justified.
  - Dependency: confirmed SIH requirement and language test images.
  - Verify: requirement decision and measured OCR result are recorded.

- [ ] Evaluate perspective/rotation correction only if test evidence justifies it.
  - Purpose: avoid adding CV transformations without a demonstrated failure case.
  - Affected: possible future preprocessing module and tests.
  - Dependency: repeatable skew/rotation failures.
  - Verify: baseline-versus-change measurements justify any implementation.

- [ ] Evaluate Tesseract provider-integration cleanup.
  - Purpose: resolve the split active Tesseract paths without disturbing Paddle behavior.
  - Affected: `src/ocr/engine.py`, `tesseract_engine.py`, tests.
  - Dependency: tests covering both engines.
  - Verify: one defined Tesseract contract passes without changing Paddle’s single-pass behavior.

- [ ] Remove `src/ocr/normalizer.py` only after confirming it remains unused.
  - Purpose: remove confirmed dead code safely.
  - Affected: `src/ocr/normalizer.py`, imports/tests/context.
  - Dependency: import/call-site audit and regression tests.
  - Verify: repository search finds no use and tests pass after authorized removal.

## P4 — Product & Database Evolution

- [ ] Audit JSON repository limitations.
  - Purpose: document durability, corruption, concurrency, and scaling limits.
  - Affected: `src/repository/store.py`, documentation.
  - Dependency: expected usage/deployment requirements.
  - Verify: a decision record identifies limits that require action.

- [ ] Add safe persistence/concurrency handling if required.
  - Purpose: protect JSON writes only when the audit demonstrates a real need.
  - Affected: `src/repository/store.py`, tests.
  - Dependency: JSON limitation audit.
  - Verify: concurrent/failure scenario is reproduced and protected by tests.

- [ ] Define a database abstraction boundary.
  - Purpose: make a future repository replacement possible without changing analysis logic.
  - Affected: `src/repository/`, `app/services/product_service.py`, documentation.
  - Dependency: JSON limitation audit.
  - Verify: service-facing operations are documented and covered by tests.

- [ ] Evaluate SQLite migration.
  - Purpose: choose a local durable database only if JSON limitations warrant it.
  - Affected: repository implementation, migration plan, tests.
  - Dependency: database abstraction and explicit need.
  - Verify: migration decision includes data compatibility and rollback plan.

- [ ] Evaluate PostgreSQL migration only if deployment scale requires it.
  - Purpose: avoid premature distributed-database complexity.
  - Affected: deployment/database documentation.
  - Dependency: confirmed multi-user or deployed-scale requirement.
  - Verify: capacity/deployment rationale exists before implementation.

- [ ] Preserve permanent scan-image storage semantics.
  - Purpose: retain per-product/per-scan copies regardless of repository implementation.
  - Affected: `app/services/product_service.py`, repository migration tests.
  - Dependency: any persistence migration.
  - Verify: migrated flow retains permanent paths and rollback behavior.

## P5 — Testing & Quality

- [ ] Add unit tests for OCR conversion.
  - Purpose: validate normalized Paddle lines become the active DataFrame schema.
  - Affected: `src/ocr/engine.py`, new tests.
  - Dependency: test harness.
  - Verify: text, confidence, and all coordinate columns are asserted.

- [ ] Add tests for coordinate scaling.
  - Purpose: protect original-to-processed coordinate alignment.
  - Affected: `src/ocr/engine.py`, `paddle_engine.py`, tests.
  - Dependency: test harness.
  - Verify: known boxes scale correctly at 1.5 and internal-resize scale factors.

- [ ] Add tests for region detection.
  - Purpose: protect existing heading-based coordinate heuristics.
  - Affected: `src/ocr/regions.py`, tests.
  - Dependency: DataFrame fixtures.
  - Verify: nutrition, ingredients, allergens, and compliance regions are asserted.

- [ ] Add tests for nutrition spatial association.
  - Purpose: preserve same-row matching and the historical Energy 522 kcal case.
  - Affected: `src/food_analysis/nutrition.py`, tests.
  - Dependency: DataFrame fixtures.
  - Verify: neighboring rows and percentage values are not misassigned.

- [ ] Add tests for ingredient and allergen extraction.
  - Purpose: protect current heuristic parsing behavior.
  - Affected: food-analysis modules, tests.
  - Dependency: test harness.
  - Verify: parentheses, stop phrases, `Contains`, and `May Contains` cases pass.

- [ ] Add tests for compliance evidence.
  - Purpose: verify matched text, confidence, and bounding-box attachment.
  - Affected: compliance modules, tests.
  - Dependency: DataFrame fixtures.
  - Verify: evidence and `REVIEW`/`NOT_FOUND` fallbacks are asserted.

- [ ] Add an end-to-end image-analysis test.
  - Purpose: exercise the active pipeline with a stable local image.
  - Affected: `app/main.py`, test assets, tests.
  - Dependency: dependencies/test harness and deterministic OCR strategy.
  - Verify: expected stable contract fields are checked without overfitting mutable OCR text.

- [ ] Add an API integration test.
  - Purpose: validate upload, analysis envelope, product scan persistence, and scan detail.
  - Affected: `app/api.py`, services, tests.
  - Dependency: P0 and test harness.
  - Verify: an isolated test repository/storage path is used and cleaned safely.

- [ ] Define a representative test-image set.
  - Purpose: separate maintained fixtures from ignored ad-hoc local images.
  - Affected: test assets, documentation, `.gitignore` only if explicitly needed.
  - Dependency: test-harness decision and image-use permissions.
  - Verify: each fixture has a stated scenario and expected non-legal assertions.

- [ ] Define basic accuracy and regression metrics.
  - Purpose: make OCR/heuristic changes measurable.
  - Affected: tests, documentation.
  - Dependency: representative test-image set.
  - Verify: baseline metrics and acceptable regressions are documented.

## P6 — Frontend Integration

- [ ] Freeze backend API response contracts.
  - Purpose: stabilize successful and quality-rejected response shapes before frontend coupling.
  - Affected: `app/api.py`, reporting, API documentation, tests.
  - Dependency: P0 OCR persistence and API integration tests.
  - Verify: documented schemas cover all endpoints and error/quality states.

- [ ] Document analyze endpoint request and response.
  - Purpose: provide exact multipart and response-contract guidance.
  - Affected: `docs/api.md`, API tests.
  - Dependency: frozen API contract.
  - Verify: documentation matches a tested request.

- [ ] Document product and scan endpoints.
  - Purpose: define product lifecycle and scan-detail contracts for clients.
  - Affected: `docs/api.md`, API tests.
  - Dependency: frozen API contract.
  - Verify: every implemented route has input, success, and error documentation.

- [ ] Define frontend error states.
  - Purpose: make upload, validation, not-found, and server-error responses actionable.
  - Affected: API documentation and frontend contract.
  - Dependency: endpoint documentation.
  - Verify: a response-to-UI-state mapping is documented.

- [ ] Define image-quality failure UX.
  - Purpose: expose rejection reasons without calling them a legal result.
  - Affected: API documentation and frontend contract.
  - Dependency: frozen quality-rejection contract.
  - Verify: acceptance/rejection fields map to a documented user flow.

- [ ] Define compliance evidence display.
  - Purpose: allow clients to show text/confidence/bounding-box evidence for human review.
  - Affected: API documentation, frontend contract.
  - Dependency: frozen evidence semantics.
  - Verify: evidence coordinates and manual-review disclaimer are documented.

- [ ] Define scan-history UI contract.
  - Purpose: support product history and individual scan details.
  - Affected: product/scan endpoint documentation, frontend contract.
  - Dependency: frozen product/scan response contracts.
  - Verify: list, detail, and missing-resource states are documented.

## P7 — Deployment / Demo Readiness

- [ ] Verify clean-environment installation.
  - Purpose: demonstrate reproducible setup.
  - Affected: `requirements.txt`, setup documentation.
  - Dependency: repaired requirements.
  - Verify: a fresh environment installs and imports the application.

- [ ] Verify dependency installation.
  - Purpose: confirm all runtime dependencies resolve together.
  - Affected: `requirements.txt`.
  - Dependency: clean-environment installation task.
  - Verify: documented install command completes successfully.

- [ ] Verify FastAPI startup.
  - Purpose: confirm the deployment entry point loads.
  - Affected: `app/api.py`, deployment documentation.
  - Dependency: repaired requirements.
  - Verify: `uvicorn app.api:app` starts and `GET /` returns the health envelope.

- [ ] Verify representative analysis flow.
  - Purpose: run one supported image through the active API/pipeline.
  - Affected: active API/pipeline and selected test asset.
  - Dependency: P0, requirements, and test-image selection.
  - Verify: response contains quality, structured analysis, and disclaimer fields.

- [ ] Verify product-history flow.
  - Purpose: demonstrate create → scan → list/detail history.
  - Affected: API, service, repository.
  - Dependency: P0 and API contract documentation.
  - Verify: one manual/demo flow returns a stored scan through history and detail routes.

- [ ] Verify permanent image retrieval and storage.
  - Purpose: confirm demo scans reference durable paths.
  - Affected: product service, repository, deployment setup.
  - Dependency: product-history flow.
  - Verify: stored scan path exists after temporary upload cleanup.

- [ ] Clean stale demo/test data.
  - Purpose: remove obsolete temporary references and generated noise only with explicit approval.
  - Affected: `data/`, `results/`, local images.
  - Dependency: user-approved deletion scope and preserved representative fixtures.
  - Verify: exact removed paths and recovery status are reported.

- [ ] Remove unnecessary debug artifacts from the demo path.
  - Purpose: prevent generated debug output from obscuring the demonstration.
  - Affected: reporting configuration/output handling, documentation.
  - Dependency: confirmed demo requirements.
  - Verify: demo flow retains needed evidence without uncontrolled debug artifacts.

- [ ] Create final SIH demo test set.
  - Purpose: select representative supported scenarios for the project demonstration.
  - Affected: approved test assets, documentation.
  - Dependency: test-image policy and representative-scenario definition.
  - Verify: each image has documented non-legal expected behavior.

- [ ] Run complete backend regression before frontend integration.
  - Purpose: establish a stable backend baseline.
  - Affected: test suite and deployment checklist.
  - Dependency: P1/P5 automated tests.
  - Verify: the complete documented test command passes.

## Deferred / Future

- [ ] Remove confirmed dead code.
  - Purpose: clean obsolete modules only after active-path and migration confirmation.
  - Affected: `src/ocr/normalizer.py`, legacy root scripts, unreachable extractor code.
  - Dependency: P3 cleanup audit and regression coverage.
  - Verify: no active imports/calls remain and tests pass.

- [ ] Evaluate advanced OCR normalization.
  - Purpose: consider normalization only for measured OCR failures.
  - Affected: OCR modules and tests.
  - Dependency: documented failure cases.
  - Verify: measured improvement without duplicate OCR inference.

- [ ] Evaluate advanced multilingual support.
  - Purpose: extend language coverage only when required.
  - Affected: OCR configuration, test assets, documentation.
  - Dependency: confirmed requirement and representative images.
  - Verify: language-specific benchmark result.

- [ ] Evaluate advanced computer vision.
  - Purpose: consider perspective, rotation, or other CV only for demonstrated failures.
  - Affected: preprocessing/vision modules and tests.
  - Dependency: failure evidence and baseline metrics.
  - Verify: documented measured benefit.

- [ ] Evaluate database scaling.
  - Purpose: revisit SQLite/PostgreSQL when usage demands it.
  - Affected: repository/deployment architecture.
  - Dependency: P4 audit and deployment scale evidence.
  - Verify: approved migration decision.

- [ ] Add authentication and authorization.
  - Purpose: protect deployed product/scan access when user roles are required.
  - Affected: API, deployment, frontend contract.
  - Dependency: deployment and access-control requirements.
  - Verify: role/access tests pass.

- [ ] Add production observability.
  - Purpose: provide safe operational diagnostics for deployed service.
  - Affected: API/deployment configuration.
  - Dependency: deployment environment and privacy requirements.
  - Verify: approved health/error telemetry works without exposing scan data.

- [ ] Evaluate cloud deployment.
  - Purpose: choose hosting only after API, storage, and security requirements are stable.
  - Affected: deployment configuration and documentation.
  - Dependency: demo/deployment requirements.
  - Verify: deployment plan includes persistent storage, secrets, and rollback.
