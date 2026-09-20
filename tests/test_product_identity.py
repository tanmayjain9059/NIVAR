import pandas as pd

from src.product_intelligence.identity import identify_product


def make_ocr(rows):
    return pd.DataFrame(rows)


def test_explicit_product_name_is_selected():
    ocr = make_ocr([
        {
            "text": "Product Name: Premium Basmati Rice",
            "conf": 0.96,
            "left": 50,
            "top": 50,
            "right": 500,
            "bottom": 100,
        },
        {
            "text": "Net Quantity 5 kg",
            "conf": 0.98,
            "left": 50,
            "top": 500,
            "right": 300,
            "bottom": 550,
        },
    ])

    result = identify_product(
        "Product Name: Premium Basmati Rice Net Quantity 5 kg",
        ocr,
    )

    assert result["product_name"] == "Premium Basmati Rice"
    assert result["product_name_evidence"]["text"] == (
        "Product Name: Premium Basmati Rice"
    )


def test_explicit_brand_is_extracted():
    ocr = make_ocr([
        {
            "text": "Brand: Fortune",
            "conf": 0.94,
            "left": 30,
            "top": 40,
            "right": 250,
            "bottom": 90,
        }
    ])

    result = identify_product(
        "Brand: Fortune",
        ocr,
    )

    assert result["brand"] == "Fortune"
    assert result["brand_evidence"]["text"] == "Brand: Fortune"


def test_noise_is_not_selected_as_product_name():
    ocr = make_ocr([
        {
            "text": "MRP ₹250",
            "conf": 0.99,
            "left": 20,
            "top": 20,
            "right": 250,
            "bottom": 70,
        },
        {
            "text": "NET QTY 1 kg",
            "conf": 0.99,
            "left": 20,
            "top": 80,
            "right": 250,
            "bottom": 130,
        },
    ])

    result = identify_product(
        "MRP ₹250 NET QTY 1 kg",
        ocr,
    )

    assert result["product_name"] is None


def test_product_evidence_contains_bbox():
    ocr = make_ocr([
        {
            "text": "Premium Rice",
            "conf": 0.91,
            "left": 100,
            "top": 200,
            "right": 400,
            "bottom": 260,
        }
    ])

    result = identify_product(
        "Premium Rice",
        ocr,
    )

    evidence = result["product_name_evidence"]

    assert evidence is not None
    assert evidence["bbox"] == {
        "x1": 100,
        "y1": 200,
        "x2": 400,
        "y2": 260,
    }
