"""
JSON and PDF report generation for the packaged-commodity analyzer.

The PDF generator consumes an already-created structured analysis result.
It does not perform OCR, image analysis, or compliance validation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# STRUCTURED JSON RESULT
# ============================================================


def build_structured_result(
    file_path,
    ocr_summary,
    nutrition,
    ingredients,
    contains,
    may_contain,
    compliance_report,
    nutrients_total,
):
    return {
        "source_image": str(file_path),
        "ocr": ocr_summary,
        "legal_metrology_compliance": compliance_report,
        "brand": None,
        "product_name": None,
        "ingredients": ingredients,
        "allergens": {
            "contains": contains,
            "may_contain": may_contain,
        },
        "nutrition": {
            nutrient: {
                "value": item["value"],
                "unit": item["unit"],
            }
            for nutrient, item in nutrition.items()
        },
        "quantity": None,
        "manufacturer": None,
        "manufacturing_date": None,
        "expiry_date": None,
        "meta": {
            "nutrition_fields_found": len(nutrition),
            "nutrition_fields_total": nutrients_total,
            "ingredients_found": len(ingredients),
            "confirmed_allergens": len(contains),
            "possible_allergens": len(may_contain),
        },
    }


def save_json_result(
    result,
    source_image_path,
    output_dir="results",
):
    output_path = Path(output_dir)
    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    stem = Path(source_image_path).stem

    result_file = output_path / f"{stem}_result.json"

    with open(
        result_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"Structured result saved to: {result_file}"
    )

    return result_file


# ============================================================
# PDF CONSTANTS
# ============================================================


CORE_DECLARATIONS = (
    (
        "manufacturer_packer_importer",
        "Manufacturer / Packer / Importer",
    ),
    (
        "net_quantity",
        "Net Quantity",
    ),
    (
        "manufacture_date",
        "Manufacture / Packing Date",
    ),
    (
        "mrp",
        "Maximum Retail Price (MRP)",
    ),
    (
        "consumer_care",
        "Consumer Care Details",
    ),
)


# ============================================================
# SAFE VALUE HELPERS
# ============================================================


def _safe_text(
    value: Any,
    fallback: str = "Not available",
) -> str:
    """
    Convert arbitrary stored JSON values into safe report text.
    """

    if value is None:
        return fallback

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, (dict, list)):
        try:
            return json.dumps(
                value,
                ensure_ascii=False,
                default=str,
            )
        except Exception:
            return str(value)

    text = str(value).strip()

    return text if text else fallback


def _escape(
    value: Any,
    fallback: str = "Not available",
) -> str:
    """
    Escape text for ReportLab Paragraph markup.
    """

    from xml.sax.saxutils import escape

    return escape(
        _safe_text(
            value,
            fallback,
        )
    )


def _status(value: Any) -> str:
    """
    Normalize a compliance status for display.
    """

    normalized = str(
        value or ""
    ).strip().upper()

    if normalized in {
        "FOUND",
        "REVIEW",
        "NOT_FOUND",
        "COMPLIANT",
        "NON_COMPLIANT",
        "PASS",
    }:
        return normalized

    return "REVIEW"


def _status_display(status: str) -> str:
    mapping = {
        "FOUND": "FOUND",
        "REVIEW": "REVIEW",
        "NOT_FOUND": "NOT FOUND",
        "COMPLIANT": "COMPLIANT",
        "NON_COMPLIANT": "NON-COMPLIANT",
        "PASS": "PASS",
    }

    return mapping.get(
        status,
        status.replace(
            "_",
            " ",
        ),
    )


def _status_color(status: str):
    """
    Use semantic status colors only inside the PDF.
    """

    if status in {
        "FOUND",
        "COMPLIANT",
        "PASS",
    }:
        return colors.HexColor("#15803D")

    if status == "REVIEW":
        return colors.HexColor("#B45309")

    if status in {
        "NOT_FOUND",
        "NON_COMPLIANT",
    }:
        return colors.HexColor("#B91C1C")

    return colors.HexColor("#52525Z".replace("Z", ""))


# ============================================================
# COMPLIANCE HELPERS
# ============================================================


def _extract_checks(
    compliance: Any,
) -> dict[str, Any]:
    if not isinstance(
        compliance,
        dict,
    ):
        return {}

    checks = compliance.get(
        "checks"
    )

    return (
        checks
        if isinstance(checks, dict)
        else {}
    )


def _extract_evidence(
    check: Any,
) -> dict[str, Any]:
    if not isinstance(
        check,
        dict,
    ):
        return {}

    evidence = check.get(
        "evidence"
    )

    return (
        evidence
        if isinstance(evidence, dict)
        else {}
    )


def _extract_detected_value(
    check: Any,
) -> Any:
    if not isinstance(
        check,
        dict,
    ):
        return None

    matched_text = check.get(
        "matched_text"
    )

    if matched_text is not None:
        return matched_text

    return check.get(
        "value"
    )


def _extract_confidence(
    check: Any,
) -> Any:
    if not isinstance(
        check,
        dict,
    ):
        return None

    evidence = _extract_evidence(
        check
    )

    confidence = evidence.get(
        "confidence"
    )

    if isinstance(
        confidence,
        (int, float),
    ):
        return confidence

    confidence = check.get(
        "confidence"
    )

    if isinstance(
        confidence,
        (int, float),
    ):
        return confidence

    return None


def _format_confidence(
    value: Any,
) -> str:
    if not isinstance(
        value,
        (int, float),
    ):
        return "Not available"

    if 0 <= value <= 1:
        return f"{value * 100:.1f}%"

    return f"{value:.1f}%"


def _extract_evidence_text(
    check: Any,
) -> Any:
    if not isinstance(
        check,
        dict,
    ):
        return None

    evidence = _extract_evidence(
        check
    )

    return (
        evidence.get("text")
        or evidence.get("matched_text")
        or evidence.get("value")
        or check.get("evidence_text")
    )


def _list_to_text(
    value: Any,
) -> str:
    if not isinstance(
        value,
        list,
    ):
        return _safe_text(value)

    if not value:
        return "None detected"

    return ", ".join(
        _safe_text(item)
        for item in value
    )


# ============================================================
# PDF STYLES
# ============================================================


def _build_styles():
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            alignment=TA_CENTER,
            spaceAfter=5 * mm,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#71717A"),
            spaceAfter=7 * mm,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#18181B"),
            spaceBefore=3 * mm,
            spaceAfter=3 * mm,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#27272A"),
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#71717A"),
        ),
        "label": ParagraphStyle(
            "Label",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#71717A"),
        ),
        "value": ParagraphStyle(
            "Value",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#18181B"),
        ),
        "status": ParagraphStyle(
            "Status",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
        ),
    }


# ============================================================
# GENERIC PDF HELPERS
# ============================================================


def _section_heading(
    title: str,
    styles,
) -> list:
    return [
        Spacer(
            1,
            3 * mm,
        ),
        Paragraph(
            _escape(title),
            styles["section"],
        ),
        HRFlowable(
            width="100%",
            thickness=0.6,
            color=colors.HexColor("#E4E4E7"),
            spaceAfter=3 * mm,
        ),
    ]


def _key_value_table(
    rows: list[tuple[str, Any]],
    styles,
):
    table_data = []

    for label, value in rows:
        table_data.append(
            [
                Paragraph(
                    _escape(label),
                    styles["label"],
                ),
                Paragraph(
                    _escape(value),
                    styles["value"],
                ),
            ]
        )

    if not table_data:
        table_data.append(
            [
                Paragraph(
                    "No data",
                    styles["small"],
                ),
                Paragraph(
                    "Not available",
                    styles["small"],
                ),
            ]
        )

    table = Table(
        table_data,
        colWidths=[
            45 * mm,
            125 * mm,
        ],
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#F4F4F5"),
                ),
            ]
        )
    )

    return table


# ============================================================
# PRODUCT IMAGE
# ============================================================


def _product_image(
    image_path: Path,
    styles,
):
    if not image_path.exists():
        return Paragraph(
            "Stored scan image is not available.",
            styles["small"],
        )

    try:
        image = Image(
            str(image_path)
        )

        max_width = 170 * mm
        max_height = 95 * mm

        width = float(
            image.imageWidth
        )
        height = float(
            image.imageHeight
        )

        if width <= 0 or height <= 0:
            return Paragraph(
                "Stored scan image could not be read.",
                styles["small"],
            )

        scale = min(
            max_width / width,
            max_height / height,
            1.0,
        )

        image.drawWidth = width * scale
        image.drawHeight = height * scale

        return image

    except Exception:
        return Paragraph(
            "Stored scan image could not be embedded.",
            styles["small"],
        )


# ============================================================
# OVERALL COMPLIANCE
# ============================================================


def _overall_status_block(
    compliance: dict[str, Any],
    styles,
):
    status = _status(
        compliance.get(
            "overall_status"
        )
    )

    detected = compliance.get(
        "mandatory_declarations_detected"
    )

    total = compliance.get(
        "mandatory_declarations_total",
        5,
    )

    if detected is None:
        detected_text = "Not available"
    else:
        detected_text = (
            f"{detected} / {total}"
        )

    color = _status_color(
        status
    )

    overall_style = ParagraphStyle(
        "OverallStatus",
        parent=styles["status"],
        textColor=color,
    )

    detected_style = ParagraphStyle(
        "DetectedStatus",
        parent=styles["status"],
        textColor=colors.HexColor("#18181B"),
    )

    data = [
        [
            Paragraph(
                "OVERALL COMPLIANCE",
                styles["label"],
            ),
            Paragraph(
                "CORE DECLARATIONS",
                styles["label"],
            ),
        ],
        [
            Paragraph(
                _status_display(status),
                overall_style,
            ),
            Paragraph(
                _escape(detected_text),
                detected_style,
            ),
        ],
    ]

    table = Table(
        data,
        colWidths=[
            85 * mm,
            85 * mm,
        ],
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#FAFAFA"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    colors.HexColor("#E4E4E7"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#E4E4E7"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, 0),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, 0),
                    2,
                ),
                (
                    "TOPPADDING",
                    (0, 1),
                    (-1, 1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 1),
                    (-1, 1),
                    9,
                ),
            ]
        )
    )

    return table


# ============================================================
# COMPLIANCE TABLE
# ============================================================


def _compliance_table(
    compliance: dict[str, Any],
    styles,
):
    checks = _extract_checks(
        compliance
    )

    header = [
        Paragraph(
            "Declaration",
            styles["label"],
        ),
        Paragraph(
            "Status",
            styles["label"],
        ),
        Paragraph(
            "Detected value",
            styles["label"],
        ),
        Paragraph(
            "Evidence",
            styles["label"],
        ),
        Paragraph(
            "Confidence",
            styles["label"],
        ),
    ]

    rows = [header]

    for key, label in CORE_DECLARATIONS:
        check = checks.get(key)

        if not isinstance(
            check,
            dict,
        ):
            check = {}

        status = _status(
            check.get("status")
        )

        detected = _extract_detected_value(
            check
        )

        evidence = _extract_evidence_text(
            check
        )

        confidence = _extract_confidence(
            check
        )

        status_style = ParagraphStyle(
            f"ComplianceStatus_{key}",
            parent=styles["small"],
            fontName="Helvetica-Bold",
            textColor=_status_color(
                status
            ),
        )

        rows.append(
            [
                Paragraph(
                    _escape(label),
                    styles["small"],
                ),
                Paragraph(
                    _escape(
                        _status_display(
                            status
                        )
                    ),
                    status_style,
                ),
                Paragraph(
                    _escape(detected),
                    styles["small"],
                ),
                Paragraph(
                    _escape(evidence),
                    styles["small"],
                ),
                Paragraph(
                    _escape(
                        _format_confidence(
                            confidence
                        )
                    ),
                    styles["small"],
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            36 * mm,
            22 * mm,
            35 * mm,
            52 * mm,
            25 * mm,
        ],
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#F4F4F5"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#D4D4D8"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#E4E4E7"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


# ============================================================
# INGREDIENTS
# ============================================================


def _ingredients_section(
    analysis: dict[str, Any],
    styles,
):
    ingredients = analysis.get(
        "ingredients"
    )

    if not isinstance(
        ingredients,
        list,
    ):
        ingredients = []

    if ingredients:
        text = ", ".join(
            _safe_text(item)
            for item in ingredients
        )
    else:
        text = (
            "No ingredient information "
            "was stored for this scan."
        )

    return [
        Paragraph(
            "Ingredients",
            styles["label"],
        ),
        Spacer(
            1,
            1.5 * mm,
        ),
        Paragraph(
            _escape(text),
            styles["body"],
        ),
    ]


# ============================================================
# ALLERGENS
# ============================================================


def _allergen_section(
    analysis: dict[str, Any],
    styles,
):
    allergens = analysis.get(
        "allergens"
    )

    if not isinstance(
        allergens,
        dict,
    ):
        allergens = {}

    contains = allergens.get(
        "contains"
    )

    may_contain = allergens.get(
        "may_contain"
    )

    return [
        Paragraph(
            "Contains",
            styles["label"],
        ),
        Spacer(
            1,
            1.5 * mm,
        ),
        Paragraph(
            _escape(
                _list_to_text(
                    contains
                )
            ),
            styles["body"],
        ),
        Spacer(
            1,
            3 * mm,
        ),
        Paragraph(
            "May contain",
            styles["label"],
        ),
        Spacer(
            1,
            1.5 * mm,
        ),
        Paragraph(
            _escape(
                _list_to_text(
                    may_contain
                )
            ),
            styles["body"],
        ),
    ]


# ============================================================
# IMAGE QUALITY
# ============================================================


def _quality_table(
    quality: Any,
    styles,
):
    if not isinstance(
        quality,
        dict,
    ):
        return _key_value_table(
            [
                (
                    "Status",
                    "Not available",
                ),
                (
                    "Quality score",
                    "Not available",
                ),
                (
                    "Notes",
                    "Image quality information "
                    "was not stored for this scan.",
                ),
            ],
            styles,
        )

    score = quality.get(
        "score"
    )

    if isinstance(
        score,
        (int, float),
    ):
        score_text = (
            f"{score:.1f} / 100"
        )
    else:
        score_text = "Not available"

    accepted = quality.get(
        "accepted"
    )

    if accepted is True:
        accepted_text = "Accepted"
    elif accepted is False:
        accepted_text = "Rejected"
    else:
        accepted_text = "Not available"

    reasons = quality.get(
        "reasons"
    )

    if isinstance(
        reasons,
        list,
    ) and reasons:
        reason_text = " • ".join(
            _safe_text(reason)
            for reason in reasons
        )
    else:
        reason_text = (
            "No quality issues reported."
        )

    return _key_value_table(
        [
            (
                "Status",
                accepted_text,
            ),
            (
                "Quality score",
                score_text,
            ),
            (
                "Notes",
                reason_text,
            ),
        ],
        styles,
    )


# ============================================================
# OCR
# ============================================================


def _ocr_section(
    analysis: dict[str, Any],
    styles,
):
    """
    Always return a list of flowables.

    This is important because the caller uses story.extend().
    """

    ocr = analysis.get(
        "ocr"
    )

    # Support persisted results where OCR may be nested
    # inside meta.
    if not isinstance(
        ocr,
        dict,
    ):
        meta = analysis.get(
            "meta"
        )

        if isinstance(
            meta,
            dict,
        ):
            meta_ocr = meta.get(
                "ocr"
            )

            if isinstance(
                meta_ocr,
                dict,
            ):
                ocr = meta_ocr

    if not isinstance(
        ocr,
        dict,
    ):
        return [
            Paragraph(
                "OCR information was not stored for this scan.",
                styles["small"],
            )
        ]

    engine = (
        ocr.get("engine")
        or ocr.get("provider")
    )

    count = (
        ocr.get("count")
        if ocr.get("count") is not None
        else ocr.get("total_boxes")
    )

    raw_text = (
        ocr.get("raw_text")
        or ocr.get("text")
    )

    elements = [
        _key_value_table(
            [
                (
                    "Engine",
                    _safe_text(engine),
                ),
                (
                    "Detected boxes",
                    _safe_text(count),
                ),
            ],
            styles,
        )
    ]

    if raw_text:
        elements.extend(
            [
                Spacer(
                    1,
                    3 * mm,
                ),
                Paragraph(
                    "Extracted text",
                    styles["label"],
                ),
                Spacer(
                    1,
                    1.5 * mm,
                ),
                Paragraph(
                    _escape(raw_text),
                    styles["small"],
                ),
            ]
        )

    return elements


# ============================================================
# PDF GENERATION
# ============================================================


def generate_pdf_report(
    analysis: dict[str, Any],
    image_path: str | Path,
    output_path: str | Path,
) -> Path:
    """
    Generate a PDF report from an already-persisted analysis.

    This function does NOT run OCR, preprocessing, extraction,
    validation, or any other analysis.
    """

    if not isinstance(
        analysis,
        dict,
    ):
        raise ValueError(
            "Stored analysis is invalid or unavailable."
        )

    image_path = Path(
        image_path
    )

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    styles = _build_styles()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Packaged Commodity Compliance Report",
        author="Packaged Commodity Compliance Analyzer",
        subject=(
            "AI-assisted Legal Metrology "
            "compliance assessment"
        ),
    )

    story = []

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    story.extend(
        [
            Paragraph(
                "PACKAGED COMMODITY<br/>"
                "COMPLIANCE REPORT",
                styles["title"],
            ),
            Paragraph(
                "AI-Assisted Legal Metrology Assessment",
                styles["subtitle"],
            ),
        ]
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    meta = analysis.get(
        "meta"
    )

    if not isinstance(
        meta,
        dict,
    ):
        meta = {}

    report_timestamp = (
        datetime.now()
        .astimezone()
        .strftime(
            "%d %b %Y, %I:%M %p"
        )
    )

    story.append(
        _key_value_table(
            [
                (
                    "Product",
                    analysis.get(
                        "product_name"
                    )
                    or "Unnamed Product",
                ),
                (
                    "Brand",
                    analysis.get(
                        "brand"
                    ),
                ),
                (
                    "Manufacturer",
                    analysis.get(
                        "manufacturer"
                    ),
                ),
                (
                    "Barcode",
                    analysis.get(
                        "barcode"
                    ),
                ),
                (
                    "Net Quantity",
                    analysis.get(
                        "quantity"
                    ),
                ),
                (
                    "Manufacture Date",
                    analysis.get(
                        "manufacturing_date"
                    ),
                ),
                (
                    "Expiry Date",
                    analysis.get(
                        "expiry_date"
                    ),
                ),
                (
                    "Report Generated",
                    report_timestamp,
                ),
            ],
            styles,
        )
    )

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    story.extend(
        _section_heading(
            "Scanned Product",
            styles,
        )
    )

    story.append(
        _product_image(
            image_path,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    # --------------------------------------------------------
    # COMPLIANCE
    # --------------------------------------------------------

    compliance = analysis.get(
        "legal_metrology_compliance"
    )

    if not isinstance(
        compliance,
        dict,
    ):
        compliance = {}

    story.extend(
        _section_heading(
            "Legal Metrology Compliance",
            styles,
        )
    )

    story.append(
        _overall_status_block(
            compliance,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    story.append(
        _compliance_table(
            compliance,
            styles,
        )
    )

    disclaimer = compliance.get(
        "disclaimer"
    )

    if disclaimer:
        story.extend(
            [
                Spacer(
                    1,
                    4 * mm,
                ),
                Paragraph(
                    _escape(disclaimer),
                    styles["small"],
                ),
            ]
        )

    # --------------------------------------------------------
    # FOOD INFORMATION
    #
    # Deliberately NOT using KeepTogether or a one-row
    # two-column table. Long ingredient/evidence text must
    # be allowed to flow naturally across pages.
    # --------------------------------------------------------

    story.append(
        PageBreak()
    )

    story.extend(
        _section_heading(
            "Ingredients & Allergen Analysis",
            styles,
        )
    )

    story.extend(
        _ingredients_section(
            analysis,
            styles,
        )
    )

    story.extend(
        [
            Spacer(
                1,
                5 * mm,
            ),
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=colors.HexColor("#E4E4E7"),
                spaceAfter=4 * mm,
            ),
        ]
    )

    story.extend(
        _allergen_section(
            analysis,
            styles,
        )
    )

    # --------------------------------------------------------
    # NUTRITION
    # --------------------------------------------------------

    story.extend(
        _section_heading(
            "Advanced Nutrition Analysis",
            styles,
        )
    )

    nutrition_table = Table(
        [
            [
                Paragraph(
                    "<b>Coming Soon</b>",
                    styles["body"],
                ),
                Paragraph(
                    _escape(
                        "Detailed extraction of calories, "
                        "macronutrients and nutrition-table "
                        "values will be available in a future version."
                    ),
                    styles["body"],
                ),
            ]
        ],
        colWidths=[
            30 * mm,
            140 * mm,
        ],
        hAlign="LEFT",
    )

    nutrition_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    colors.HexColor("#FEF3C7"),
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    colors.HexColor("#FFFBEB"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#FDE68A"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(
        nutrition_table
    )

    # --------------------------------------------------------
    # IMAGE QUALITY
    # --------------------------------------------------------

    story.extend(
        _section_heading(
            "Image Quality",
            styles,
        )
    )

    quality = (
        analysis.get(
            "image_quality"
        )
        or meta.get(
            "image_quality"
        )
    )

    story.append(
        _quality_table(
            quality,
            styles,
        )
    )

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    story.extend(
        _section_heading(
            "OCR Summary",
            styles,
        )
    )

    story.extend(
        _ocr_section(
            analysis,
            styles,
        )
    )

    # --------------------------------------------------------
    # FOOTER / DISCLAIMER
    # --------------------------------------------------------

    story.extend(
        [
            Spacer(
                1,
                8 * mm,
            ),
            HRFlowable(
                width="100%",
                thickness=0.6,
                color=colors.HexColor("#D4D4D8"),
                spaceAfter=3 * mm,
            ),
            Paragraph(
                _escape(
                    "This report is an AI-assisted first-pass "
                    "assessment based on OCR and automated rule "
                    "evaluation. It is intended to support screening "
                    "and review and does not constitute legal "
                    "certification or a final determination of compliance."
                ),
                styles["small"],
            ),
        ]
    )

    # --------------------------------------------------------
    # PAGE FOOTER
    # --------------------------------------------------------

    def draw_page_footer(
        canvas,
        document,
    ):
        canvas.saveState()

        canvas.setFont(
            "Helvetica",
            7,
        )

        canvas.setFillColor(
            colors.HexColor("#71717A")
        )

        canvas.drawString(
            20 * mm,
            10 * mm,
            "Packaged Commodity Compliance Analyzer",
        )

        canvas.drawRightString(
            A4[0] - 20 * mm,
            10 * mm,
            f"Page {document.page}",
        )

        canvas.restoreState()

    # --------------------------------------------------------
    # BUILD
    # --------------------------------------------------------

    doc.build(
        story,
        onFirstPage=draw_page_footer,
        onLaterPages=draw_page_footer,
    )

    return output_path