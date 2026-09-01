# Food Label Analyzer

> **OCR-based packaged food label analysis and preliminary Legal Metrology compliance screening system**

Food Label Analyzer is a Python-based computer vision and OCR system designed to analyze images of packaged food products and extract important information printed on their labels.

The system combines **OpenCV**, **Tesseract OCR**, structured text extraction, region-of-interest detection, and rule-based compliance analysis to transform an image of a packaged commodity into structured information.

The primary objective of the project is to support the development of a software system for checking packaged commodities against declaration requirements relevant to the **Legal Metrology (Packaged Commodities) Rules, 2011**.

In addition to the primary compliance workflow, the project provides secondary food-label intelligence including:

- Nutrition information extraction
- Ingredient extraction
- Allergen detection
- Structured JSON output
- OCR region visualization
- Debugging images
- Automated preliminary compliance reporting

---

# Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Project Objective](#project-objective)
- [How the System Works](#how-the-system-works)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Processing Pipeline](#processing-pipeline)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Tesseract OCR Setup](#tesseract-ocr-setup)
- [Running the Project](#running-the-project)
- [Example Workflow](#example-workflow)
- [OCR Pipeline](#ocr-pipeline)
- [Section Detection](#section-detection)
- [Nutrition Analysis](#nutrition-analysis)
- [Ingredient Analysis](#ingredient-analysis)
- [Allergen Analysis](#allergen-analysis)
- [Legal Metrology Compliance](#legal-metrology-compliance)
- [Compliance Statuses](#compliance-statuses)
- [Structured Output](#structured-output)
- [Debug Output](#debug-output)
- [Current Capabilities](#current-capabilities)
- [Known Limitations](#known-limitations)
- [Development Status](#development-status)
- [Roadmap](#roadmap)
- [Testing Strategy](#testing-strategy)
- [Design Decisions](#design-decisions)
- [Future Architecture](#future-architecture)
- [SIH PS 34 Alignment](#sih-ps-34-alignment)
- [Responsible Use](#responsible-use)
- [Contributing](#contributing)
- [License](#license)

---

# Overview

Packaged food labels contain a large amount of information that may be important for consumers, regulators, manufacturers, and compliance teams.

This information is often presented in different layouts, font sizes, orientations, colors, and backgrounds.

A computer vision system must therefore solve several problems:

1. Read text from a package image.
2. Locate important sections of the label.
3. Extract structured information from those sections.
4. Identify declarations relevant to packaged-commodity compliance.
5. Present the extracted information in a machine-readable format.
6. Provide enough evidence for a human reviewer to verify the result.

Food Label Analyzer is being developed around this pipeline.

---

# Problem Statement

The project is primarily motivated by the need for an automated software system capable of assisting with the verification of packaged commodities.

Manual inspection of packaging can be:

- Time-consuming
- Repetitive
- Difficult to scale
- Susceptible to human oversight
- Difficult to standardize across large numbers of products

A computer vision and OCR-based workflow can help automate the first stage of this process.

The system accepts an image of a packaged food product and attempts to identify and extract declarations such as:

- Manufacturer / packer / importer
- Net quantity
- MRP
- Manufacturing / packing information
- Consumer care information
- Country of origin where applicable
- Product / commodity identification

The system additionally extracts food-label information such as:

- Ingredients
- Nutrition values
- Allergens

---

# Project Objective

The main objective is to build an extensible software pipeline that can:

```text
Image
  ↓
Image Preprocessing
  ↓
OCR
  ↓
Section Detection
  ↓
Information Extraction
  ↓
Compliance Rules
  ↓
Structured Result
  ↓
Human Verification








vv
