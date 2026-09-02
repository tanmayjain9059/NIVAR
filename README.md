# Food Label Analyzer

> OCR-based packaged commodity analysis and preliminary Legal Metrology compliance screening system

Food Label Analyzer is a Python-based computer vision and OCR system being developed for **Smart India Hackathon 2026 – Problem Statement SIH26034**.

The system analyzes images of packaged commodities and extracts information printed on their labels. It combines image preprocessing, OCR, spatial text analysis, structured extraction, food-label analysis, and rule-based Legal Metrology screening.

The goal is to provide an automated **first-pass compliance screening system** that can assist human reviewers in identifying declarations that are detected, require review, or are not detected in a package image.

---

## Table of Contents

- [Overview](#overview)
- [SIH Problem Statement](#sih-problem-statement)
- [Project Objective](#project-objective)
- [How It Works](#how-it-works)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Processing Pipeline](#processing-pipeline)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Analyzer](#running-the-analyzer)
- [OCR System](#ocr-system)
- [Image Quality Assessment](#image-quality-assessment)
- [Section Detection](#section-detection)
- [Nutrition Analysis](#nutrition-analysis)
- [Ingredient Analysis](#ingredient-analysis)
- [Allergen Analysis](#allergen-analysis)
- [Legal Metrology Compliance](#legal-metrology-compliance)
- [Compliance Statuses](#compliance-statuses)
- [OCR Evidence](#ocr-evidence)
- [Structured Output](#structured-output)
- [REST API](#rest-api)
- [Current Capabilities](#current-capabilities)
- [Known Limitations](#known-limitations)
- [Development Status](#development-status)
- [Roadmap](#roadmap)
- [SIH PS Alignment](#sih-ps-alignment)
- [Design Principles](#design-principles)
- [Responsible Use](#responsible-use)
- [Contributing](#contributing)
- [License](#license)

---

# Overview

Packaged commodity labels contain information that must be presented in a prescribed manner.

Examples include:

- Manufacturer / packer / importer details
- Net quantity
- Maximum Retail Price (MRP)
- Manufacturing / packing information
- Consumer care details
- Country of origin where applicable
- Commodity identification

Manually checking large numbers of packages can be repetitive and difficult to scale.

Food Label Analyzer uses computer vision and OCR to automate the **initial inspection stage**.

The system does not treat OCR detection alone as proof of legal compliance. Instead, it produces an evidence-aware preliminary result that can be reviewed by a human.

---

# SIH Problem Statement

This project is being developed for:

**Smart India Hackathon 2026**

**Problem Statement:** SIH26034

**Title:**

> Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.

The intended system should be able to analyze packaged commodity labels and assist in identifying:

- Mandatory declarations
- Missing declarations
- Incorrect or incomplete declarations
- Placement-related issues
- Readability and font-size issues
- Compliance violations
- Compliance evidence and reports
- Product compliance history

The current repository implements the OCR, extraction, evidence and preliminary compliance-screening foundation for this larger system.

---

# Project Objective

The current objective is to build a modular pipeline capable of converting a package image into structured, reviewable information.

```text
Package Image
      |
      v
Image Quality Assessment
      |
      v
Image Preprocessing
      |
      v
PaddleOCR
      |
      v
Text + Bounding Boxes + Confidence
      |
      v
Section Detection
      |
      v
Spatial / Semantic Extraction
      |
      v
Food Label Analysis
      |
      v
Legal Metrology Rules
      |
      v
Evidence-Aware Validation
      |
      v
Structured JSON Result
      |
      v
Android / Web Frontend
````

The architecture is intentionally modular so that additional rules, product history, dashboards and frontend clients can be added without rewriting the OCR pipeline.

---

# How It Works

## 1. Image Input

The analyzer accepts an image of a packaged commodity.

Supported formats currently include:

* JPG
* JPEG
* PNG
* WEBP

---

## 2. Image Quality Assessment

The system includes an image-quality analysis layer that evaluates basic image characteristics such as:

* Resolution
* Blur
* Brightness
* Contrast

The purpose is to determine whether an image is suitable for reliable downstream analysis.

The quality thresholds are designed to avoid unnecessarily rejecting usable package images and can be calibrated further using real-world datasets.

---

## 3. Image Preprocessing

The image is prepared for OCR using OpenCV-based preprocessing.

Current processing includes:

* Image resizing
* Image enlargement where required
* Contrast enhancement
* OCR-oriented image preparation

---

## 4. OCR

The primary OCR engine is currently **PaddleOCR**.

The OCR pipeline preserves:

* Recognized text
* Confidence score
* Bounding box coordinates

Spatial information is important because the location of text on a package provides useful contextual information.

---

## 5. Section Detection

The OCR output is used to locate logical sections such as:

* Nutrition information
* Ingredients
* Allergen information
* Compliance-related declarations

Section detection operates on OCR coordinates rather than performing OCR again on every region.

---

## 6. Structured Extraction

Detected text is converted into structured information.

For example:

```text
Energy       -> 522 kcal
Total Fat    -> 28.5 g
Protein      -> 5.2 g
Sodium       -> 592 mg
```

For Legal Metrology declarations, the system also records supporting evidence from the original OCR result where possible.

---

# Key Features

## Current

* PaddleOCR-based text recognition
* OCR confidence scores
* OCR bounding boxes
* Image preprocessing
* Image quality assessment module
* Label section detection
* Spatial nutrition extraction
* Ingredient extraction
* Allergen detection
* Legal Metrology declaration extraction
* Evidence-aware compliance validation
* `FOUND / REVIEW / NOT_FOUND` classification
* Structured JSON output
* Debug image generation
* FastAPI REST endpoint

## Planned

* Product repository
* Product and scan history
* Product identification
* Compliance history
* Evidence visualization
* Violation reports
* Enforcement dashboard
* Font-size verification
* Placement verification
* Improved rule engine
* Android integration
* Web dashboard

---

# System Architecture

```text
                    Android / Web
                          |
                          v
                     FastAPI API
                          |
                          v
              Image Quality Assessment
                          |
                          v
                    Preprocessing
                          |
                          v
                       PaddleOCR
                          |
                  +-------+-------+
                  |               |
                  v               v
                Text        Bounding Boxes
                  |               |
                  +-------+-------+
                          |
                          v
                  Section Detection
                          |
             +------------+------------+
             |            |            |
             v            v            v
         Nutrition    Ingredients   Compliance
             |            |            |
             v            v            v
        Structured    Structured   Declaration
         Analysis      Analysis     Extraction
                                         |
                                         v
                                  Rule Validation
                                         |
                                         v
                                  Evidence + Status
                                         |
                                         v
                                   JSON Response
```

---

# Processing Pipeline

```text
Upload / Capture
       |
       v
Image Quality Assessment
       |
       v
Preprocessing
       |
       v
PaddleOCR
       |
       v
OCR Text + Coordinates + Confidence
       |
       v
Section Detection
       |
       v
Spatial Extraction
       |
       +-------------------+
       |                   |
       v                   v
Food Label Analysis   Compliance Analysis
       |                   |
       +---------+---------+
                 |
                 v
        Evidence-Aware Validation
                 |
                 v
          Structured Result
                 |
                 v
             REST API
                 |
                 v
          Android / Web
```

---

# Technology Stack

| Component            | Technology                |
| -------------------- | ------------------------- |
| Programming Language | Python                    |
| Computer Vision      | OpenCV                    |
| Primary OCR          | PaddleOCR                 |
| Secondary OCR        | Tesseract OCR             |
| Data Processing      | Pandas                    |
| API Framework        | FastAPI                   |
| Validation           | Python rule-based modules |
| Output Format        | JSON                      |
| Version Control      | Git / GitHub              |
| Frontend Integration | REST API                  |

PaddleOCR is currently the primary OCR path because the system requires both text recognition and spatial information.

Tesseract remains available as a secondary OCR implementation for compatible workflows.

---

# Project Structure

```text
opencv-label-analyzer/
|
+-- app/
|   +-- __init__.py
|   +-- api.py
|   +-- main.py
|   |
|   +-- services/
|       +-- __init__.py
|       +-- analyzer_service.py
|
+-- src/
|   |
|   +-- compliance/
|   |   +-- __init__.py
|   |   +-- extractor.py
|   |   +-- rules.py
|   |   +-- validator.py
|   |
|   +-- food_analysis/
|   |   +-- __init__.py
|   |   +-- allergens.py
|   |   +-- ingredients.py
|   |   +-- nutrition.py
|   |
|   +-- image_quality/
|   |   +-- __init__.py
|   |   +-- quality.py
|   |
|   +-- ocr/
|   |   +-- __init__.py
|   |   +-- engine.py
|   |   +-- normalizer.py
|   |   +-- paddle_engine.py
|   |   +-- preprocessing.py
|   |   +-- provider.py
|   |   +-- regions.py
|   |
|   +-- reporting/
|       +-- json_report.py
|       +-- visualization.py
|
+-- docs/
+-- requirements.txt
+-- README.md
```

---

# Installation

## 1. Clone the repository

```bash
git clone <repository-url>
cd opencv-label-analyzer
```

## 2. Create a virtual environment

```bash
python3 -m venv venv
```

## 3. Activate the environment

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Analyzer

Activate the virtual environment:

```bash
source venv/bin/activate
```

Run the analyzer from the project root:

```bash
python -m app.main
```

Using:

```bash
python -m app.main
```

is preferred because the project contains both `app` and `src` packages.

---

# OCR System

The OCR architecture uses a provider-based design.

```text
OCR Provider
     |
     +-- PaddleOCR
     |
     +-- Tesseract
```

The provider layer allows the OCR implementation to be changed without rewriting the extraction modules.

PaddleOCR currently provides:

```text
Text
Confidence
Bounding Box
```

This spatial information is used by downstream extraction modules.

---

# Image Quality Assessment

The image quality module evaluates basic characteristics before or around the OCR workflow.

Current checks include:

### Resolution

Determines whether the image has sufficient dimensions for useful analysis.

### Blur

Uses image sharpness measurements based on the variance of the Laplacian.

### Brightness

Detects extremely dark or bright images.

### Contrast

Checks whether the image contains sufficient grayscale variation.

The quality module returns a structured result similar to:

```json
{
  "accepted": true,
  "score": 99.1,
  "checks": {
    "resolution": {
      "status": "PASS"
    },
    "blur": {
      "status": "PASS"
    },
    "brightness": {
      "status": "PASS"
    },
    "contrast": {
      "status": "PASS"
    }
  },
  "rejection_reasons": []
}
```

---

# Section Detection

The OCR coordinates are used to locate logical sections.

Current section detection includes:

```text
Nutrition
Ingredients
Allergens
Compliance
```

The system attempts to locate section headings and uses their spatial positions to construct approximate regions.

This allows downstream modules to work with relevant OCR content without repeatedly running OCR on every region.

---

# Nutrition Analysis

Nutrition extraction is spatially aware.

Instead of relying only on the order of OCR text, nutrient labels are matched with nearby numeric values using their bounding boxes.

For example:

```text
Energy                    522 kcal
Total Fat                  28.5 g
Protein                     5.2 g
Sodium                    592 mg
```

This helps reduce OCR ordering errors where a numeric value from one nutrition row could otherwise be assigned to the wrong nutrient.

---

# Ingredient Analysis

The ingredient module attempts to identify and structure ingredient information from the detected ingredient region.

Ingredient extraction is currently heuristic and depends on:

* OCR quality
* Label layout
* Text orientation
* Section detection accuracy

---

# Allergen Analysis

The system attempts to detect explicit allergen declarations such as:

```text
Contains wheat
```

Allergen information is separated into:

```text
Contains
May contain
```

This module is supplementary to the primary Legal Metrology compliance workflow.

---

# Legal Metrology Compliance

The compliance module performs a **preliminary declaration screening**.

The current mandatory declaration categories include:

| Declaration                       | Purpose                                       |
| --------------------------------- | --------------------------------------------- |
| Manufacturer / packer / importer  | Identifies the responsible entity and address |
| Net quantity                      | Declared quantity of the commodity            |
| Manufacture / packing information | Month and year information                    |
| MRP                               | Retail sale price declaration                 |
| Consumer care                     | Consumer complaint/contact information        |

Conditional information includes:

```text
Country of Origin
```

Some declarations are intentionally retained for manual review when automated processing cannot establish sufficient information.

---

# Compliance Statuses

The system intentionally does **not** treat OCR detection as automatic legal compliance.

Each declaration can receive one of the following statuses.

## FOUND

The relevant declaration was detected and supporting OCR evidence is available.

```text
FOUND
```

This does **not** mean that the declaration has been legally verified.

---

## REVIEW

The system detected an indication of the declaration, but cannot confidently establish all required information.

For example:

```text
Net Weight
```

may be detected while the numerical quantity is not reliably visible.

The correct result is:

```text
REVIEW
```

rather than assuming a quantity from unrelated text.

---

## NOT_FOUND

The expected declaration could not be detected in the OCR/searchable content.

This does not prove that the declaration is physically absent from the package.

It may have been missed because of:

* OCR failure
* Image quality
* Label orientation
* Text layout
* Occlusion
* Low contrast
* Complex visual structure

---

# OCR Evidence

Compliance results can retain evidence from the OCR layer.

Evidence can contain:

```json
{
  "text": "MRP (incl. of all taxe)",
  "confidence": 0.752,
  "bbox": {
    "left": 942,
    "top": 3708,
    "right": 1982,
    "bottom": 4056
  }
}
```

This allows future frontend interfaces to highlight the source text on the original package image.

The evidence layer is important because a reviewer should be able to understand **why** the system produced a result.

---

# Structured Output

The analyzer produces a structured JSON result containing information such as:

```json
{
  "source_image": "...",
  "legal_metrology_compliance": {},
  "brand": null,
  "product_name": null,
  "ingredients": [],
  "allergens": {
    "contains": [],
    "may_contain": []
  },
  "nutrition": {},
  "quantity": null,
  "manufacturer": null,
  "manufacturing_date": null,
  "expiry_date": null,
  "meta": {}
}
```

The schema is designed to remain frontend-friendly and can be extended as additional analysis modules are added.

---

# REST API

The backend exposes a FastAPI interface for Android and Web clients.

## Health Endpoint

```http
GET /
```

## Analysis Endpoint

```http
POST /api/v1/analyze
```

The image is uploaded as multipart form data.

Example:

```bash
curl -X POST \
  http://localhost:8000/api/v1/analyze \
  -F "image=@test1.JPG"
```

The API returns a structured response containing:

```text
success
api_version
data
warnings
errors
```

Frontend clients should communicate through the API rather than importing internal Python modules.

---

# Current Capabilities

The current backend can:

* Accept package images
* Preprocess images
* Run PaddleOCR
* Preserve OCR confidence
* Preserve OCR coordinates
* Detect major label regions
* Extract nutrition values spatially
* Extract ingredients
* Detect allergens
* Extract Legal Metrology declarations
* Attach OCR evidence to declarations
* Distinguish `FOUND / REVIEW / NOT_FOUND`
* Generate structured JSON
* Generate debugging output
* Expose analysis through FastAPI

---

# Known Limitations

The current implementation is a **first-pass screening system**, not a complete legal compliance certification system.

## OCR Limitations

OCR can fail because of:

* Low-quality images
* Curved packaging
* Stylized fonts
* Reflections
* Shadows
* Occlusion
* Complex backgrounds
* Unusual orientations

## Extraction Limitations

Some declarations require stronger contextual understanding than regex and heuristic extraction can currently provide.

## Placement Verification

The current system detects approximate regions but does not yet provide complete legal placement verification.

## Font-Size Verification

Reliable legal font-size verification requires image-scale calibration and additional visual processing. This is not yet fully implemented.

## Correctness Verification

Detecting a declaration is different from verifying whether its content is legally correct.

## Product Repository

Persistent product storage and scan history are planned and are the next major development phase.

---

# Development Status

Current development stage:

```text
OCR Foundation                 [x]
Image Preprocessing            [x]
Spatial OCR                    [x]
Nutrition Extraction           [x]
Ingredient Extraction          [x]
Allergen Extraction            [x]
Image Quality Module           [x]
Compliance Extraction          [x]
Evidence-Aware Validation      [x]
Structured JSON                [x]
FastAPI Boundary               [x]

Product Repository             [ ]
Scan History                   [ ]
Evidence Visualization         [ ]
Compliance Reports             [ ]
Dashboard                      [ ]
Font Size Verification         [ ]
Placement Verification         [ ]
Advanced Rule Engine           [ ]
```

---

# Roadmap

## Phase 1 - Core Analysis

* [x] Image preprocessing
* [x] PaddleOCR integration
* [x] OCR confidence
* [x] OCR bounding boxes
* [x] Region detection
* [x] Spatial nutrition extraction
* [x] Image quality assessment
* [x] Compliance extraction
* [x] Evidence-aware validation
* [x] Structured API output

## Phase 2 - Product Repository

* [ ] Product model
* [ ] Unique internal product ID
* [ ] Product name
* [ ] Brand
* [ ] Optional barcode
* [ ] Scan ID
* [ ] Scan history
* [ ] Compliance history
* [ ] Persistent storage

Planned conceptual model:

```text
Product
|
+-- product_id
+-- product_name
+-- brand
+-- barcode (optional)
|
+-- scans[]
      |
      +-- scan_id
      +-- image
      +-- timestamp
      +-- image_quality
      +-- OCR
      +-- compliance
```

## Phase 3 - Evidence and Reporting

* [ ] Bounding-box visualization
* [ ] Violation summaries
* [ ] Compliance reports
* [ ] Human-review workflow
* [ ] Historical comparison

## Phase 4 - Advanced Compliance

* [ ] Font-size verification
* [ ] Readability assessment
* [ ] Placement verification
* [ ] Improved conditional rules
* [ ] Better declaration correctness checks
* [ ] Expanded Legal Metrology rule engine

## Phase 5 - Platform Integration

* [ ] Android application integration
* [ ] Web dashboard
* [ ] Product repository API
* [ ] Enforcement dashboard
* [ ] Authentication
* [ ] Deployment

---

# SIH PS Alignment

The architecture is designed around the major requirements of SIH26034.

| SIH Requirement                | Current Status                             |
| ------------------------------ | ------------------------------------------ |
| Scan product images            | Implemented                                |
| OCR label information          | Implemented                                |
| Detect mandatory declarations  | Implemented as preliminary screening       |
| Detect missing declarations    | Implemented                                |
| Detect incomplete declarations | Partially implemented through REVIEW       |
| Correctness verification       | In development                             |
| Placement verification         | Planned                                    |
| Readability verification       | Partially supported by OCR quality signals |
| Font-size verification         | Planned                                    |
| Compliance reports             | Structured foundation implemented          |
| Violation summaries            | Planned                                    |
| Product repository             | Next development phase                     |
| Compliance history             | Planned                                    |
| Enforcement dashboard          | Planned                                    |

The architecture deliberately separates implemented capabilities from planned capabilities.

---

# Design Principles

## 1. Evidence Before Assumptions

The system should not invent missing values.

For example:

```text
Net Weight
```

without a reliably detected quantity should produce:

```text
REVIEW
```

rather than assuming a value from another quantity such as serving size.

---

## 2. OCR Detection Is Not Legal Certification

The system is intended to support a human review process.

```text
OCR Detection
      |
      v
Automated Screening
      |
      v
Evidence
      |
      v
Human Verification
```

---

## 3. Spatial Information Matters

Text location is preserved because package compliance is not purely a text-recognition problem.

Future checks such as placement, proximity and visual verification can build on OCR bounding boxes.

---

## 4. Modular Architecture

OCR, extraction, validation, reporting and API layers are separated so that individual components can evolve independently.

---

## 5. Frontend Independence

Android and Web clients should communicate through the REST API.

The frontend should not depend directly on internal Python modules.

```text
Android / Web
      |
      v
FastAPI
      |
      v
Analysis Engine
```

This allows the backend and frontend teams to work independently.

---

# Responsible Use

Food Label Analyzer provides an **automated preliminary screening result**.

A result such as:

```text
NOT_FOUND
```

does not establish that a declaration is legally absent.

Similarly:

```text
FOUND
```

does not establish that the declaration is legally compliant.

Final enforcement or regulatory decisions should involve appropriate human verification and applicable Legal Metrology requirements.

---

# Contributing

When adding a feature:

1. Keep OCR logic inside the OCR layer.
2. Keep extraction logic inside the relevant extraction module.
3. Keep legal rules inside the compliance layer.
4. Avoid placing business logic inside the API layer.
5. Preserve the structured API response where possible.
6. Add evidence whenever an automated decision can be supported by OCR coordinates and confidence.
7. Keep frontend-specific logic outside the analysis engine.

---

# License

This project is currently under development for **Smart India Hackathon 2026**.

License information will be added when finalized by the project team.

````