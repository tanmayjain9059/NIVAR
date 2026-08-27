"""
Application entry point for the packaged-food label analyzer.

This file is intentionally thin. It orchestrates the individual
OCR, region detection, compliance, food-analysis, and reporting
modules.
"""

import sys
from pathlib import Path

import cv2
import tkinter as tk
from tkinter import filedialog

from src.ocr.preprocessing import preprocess_image
from src.ocr.engine import run_ocr, ocr_roi

from src.ocr.regions import (
    detect_nutrition_region,
    detect_ingredients_region,
    detect_allergen_region,
    detect_compliance_region,
    crop_region,
    split_region_horizontally,
)

from src.food_analysis import (
    NUTRIENTS,
    parse_nutrition_table,
    parse_ingredients,
    parse_allergens,
)

from src.compliance import validate_declarations

from src.reporting import (
    build_structured_result,
    save_json_result,
    save_debug_images,
    draw_regions,
)


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG = {
    # Image preprocessing
    "scale": 1.5,
    "polarity_dark_threshold": 110,

    # OCR
    "global_ocr_config": "--psm 11",
    "roi_ocr_config": "--psm 6",

    # ROI preprocessing
    "roi_denoise_kernel": 3,

    # Nutrition parser
    "nutrient_vertical_tolerance": 80,
    "nutrient_horizontal_max": 900,
    "nutrient_score_threshold": 1500,

    # Nutrition region
    "nutrition_left_padding": 500,
    "nutrition_top_padding": 100,
    "nutrition_right_padding": 1800,
    "nutrition_height": 1800,

    # Ingredients region
    "ingredients_left_padding": 200,
    "ingredients_top_padding": 80,
    "ingredients_right_padding": 1800,
    "ingredients_height": 1000,

    # General section spacing
    "section_gap": 30,

    # Allergen region
    "allergen_left_padding": 200,
    "allergen_top_padding": 80,
    "allergen_right_padding": 1800,
    "allergen_height": 700,

    # Compliance region
    "compliance_left_padding": 500,
    "compliance_top_padding": 100,
    "compliance_right_padding": 1800,
    "compliance_height": 2200,

    # Compliance split
    "compliance_split_ratio": 0.5,

    # Output
    "output_dir": "results",

    # GUI
    "show_gui": True,
}


# ============================================================
# IMAGE SELECTION
# ============================================================

def select_image():
    root = tk.Tk()
    root.withdraw()

    return filedialog.askopenfilename(
        title="Select Food Package Image",
        filetypes=[
            (
                "Image files",
                "*.jpg *.jpeg *.png *.webp *.JPG *.JPEG *.PNG *.WEBP",
            ),
            ("All files", "*.*"),
        ],
    )


# ============================================================
# IMAGE LOADING
# ============================================================

def load_image(file_path):
    image = cv2.imread(str(file_path))

    if image is None:
        raise ValueError(
            f"Could not load image: {file_path}"
        )

    return image


# ============================================================
# REGION CONVERSION
# ============================================================

def region_to_box(region):
    """
    Convert internal region representation into the format
    expected by the visualization layer.
    """

    if region is None:
        return None

    return {
        "x1": int(region["x"]),
        "y1": int(region["y"]),
        "x2": int(region["x"] + region["w"]),
        "y2": int(region["y"] + region["h"]),
    }


def normalize_regions(regions):
    return {
        name: region_to_box(region)
        for name, region in regions.items()
    }


# ============================================================
# PRINTING
# ============================================================

def print_sections(
    nutrition_text,
    ingredients_text,
    allergen_text,
    compliance_left_text,
    compliance_right_text,
):
    print("\n" + "=" * 36)
    print("       SECTION OCR")
    print("=" * 36)

    print("\n--- NUTRITION ---")
    print(nutrition_text)

    print("\n--- INGREDIENTS ---")
    print(ingredients_text)

    print("\n--- ALLERGENS ---")
    print(allergen_text)

    print("\n--- COMPLIANCE BLOCK (LEFT) ---")
    print(compliance_left_text)

    print("\n--- COMPLIANCE BLOCK (RIGHT) ---")
    print(compliance_right_text)


def print_results(
    nutrition,
    ingredients,
    contains,
    may_contain,
):
    print("\n" + "=" * 36)
    print("       STRUCTURED NUTRITION")
    print("=" * 36)

    if nutrition:
        for nutrient, item in nutrition.items():
            print(
                f"{nutrient:<20}: "
                f"{item['value']} {item['unit']}"
            )
    else:
        print("No reliable nutrition values found.")

    print("\n" + "=" * 36)
    print("       STRUCTURED INGREDIENTS")
    print("=" * 36)

    if ingredients:
        for index, ingredient in enumerate(
            ingredients,
            start=1,
        ):
            print(f"{index}. {ingredient}")
    else:
        print("No ingredients detected.")

    print("\n" + "=" * 36)
    print("       STRUCTURED ALLERGENS")
    print("=" * 36)

    print("\nContains:")

    if contains:
        for item in contains:
            print(f"- {item}")
    else:
        print("- None detected")

    print("\nMay contain:")

    if may_contain:
        for item in may_contain:
            print(f"- {item}")
    else:
        print("- None detected")


# ============================================================
# MAIN PIPELINE
# ============================================================

def process_image(file_path, config=CONFIG):

    print("\nImage loaded successfully!")
    print("File:", file_path)

    image = load_image(file_path)

    height, width, channels = image.shape

    print("Width:", width)
    print("Height:", height)
    print("Channels:", channels)

    # --------------------------------------------------------
    # PREPROCESSING
    # --------------------------------------------------------

    print("\nPreprocessing image...")

    processed_color, processed_gray = preprocess_image(
        image,
        config,
    )

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    data, raw_text = run_ocr(
        processed_gray,
        config,
    )

    print("\n========== RAW OCR TEXT ==========")
    print(raw_text)
    print("==================================")

    # --------------------------------------------------------
    # REGION DETECTION
    # --------------------------------------------------------

    print("\nDetecting section regions...")

    nutrition_region = detect_nutrition_region(
        processed_gray,
        data,
        config,
    )

    ingredients_region = detect_ingredients_region(
        processed_gray,
        data,
        nutrition_region,
        config,
    )

    allergen_region = detect_allergen_region(
        processed_gray,
        data,
        config,
    )

    compliance_region = detect_compliance_region(
        processed_gray,
        data,
        config,
    )

    regions = {
        "nutrition": nutrition_region,
        "ingredients": ingredients_region,
        "allergens": allergen_region,
        "compliance": compliance_region,
    }

    print("\n========== DETECTED REGIONS ==========")

    for name, region in regions.items():

        if region is None:
            print(f"{name.title()}: Not detected")
        else:
            print(
                f"{name.title()}: "
                f"({region['x']}, {region['y']}) → "
                f"({region['x'] + region['w']}, "
                f"{region['y'] + region['h']})"
            )

    print("======================================")

    # --------------------------------------------------------
    # CROP ROIS
    # --------------------------------------------------------

    rois = {
        "nutrition": crop_region(
            processed_gray,
            nutrition_region,
        ),

        "ingredients": crop_region(
            processed_gray,
            ingredients_region,
        ),

        "allergens": crop_region(
            processed_gray,
            allergen_region,
        ),

        "compliance": crop_region(
            processed_gray,
            compliance_region,
        ),
    }

    # --------------------------------------------------------
    # SPLIT COMPLIANCE REGION
    # --------------------------------------------------------

    compliance_left_roi = None
    compliance_right_roi = None

    if compliance_region is not None:

        left_region, right_region = (
            split_region_horizontally(
                compliance_region,
                config["compliance_split_ratio"],
            )
        )

        compliance_left_roi = crop_region(
            processed_gray,
            left_region,
        )

        compliance_right_roi = crop_region(
            processed_gray,
            right_region,
        )

        rois["compliance_left"] = (
            compliance_left_roi
        )

        rois["compliance_right"] = (
            compliance_right_roi
        )

    # --------------------------------------------------------
    # SECTION OCR
    # --------------------------------------------------------

    print("\nReading detected sections...")

    nutrition_text = ocr_roi(
        rois["nutrition"],
        config,
    )

    ingredients_text = ocr_roi(
        rois["ingredients"],
        config,
    )

    allergen_text = ocr_roi(
        rois["allergens"],
        config,
    )

    compliance_left_text = ocr_roi(
        compliance_left_roi,
        config,
    )

    compliance_right_text = ocr_roi(
        compliance_right_roi,
        config,
    )

    compliance_text = (
        compliance_left_text
        + "\n"
        + compliance_right_text
    )

    print_sections(
        nutrition_text,
        ingredients_text,
        allergen_text,
        compliance_left_text,
        compliance_right_text,
    )

    # --------------------------------------------------------
    # FOOD ANALYSIS
    # --------------------------------------------------------

    nutrition = parse_nutrition_table(
        rois["nutrition"],
        config,
    )

    ingredients = parse_ingredients(
        ingredients_text,
    )

    contains, may_contain = parse_allergens(
        allergen_text,
    )

    # --------------------------------------------------------
    # COMPLIANCE
    # --------------------------------------------------------

    compliance_report = validate_declarations(
        raw_text,
        compliance_text,
    )

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    print_results(
        nutrition,
        ingredients,
        contains,
        may_contain,
    )

    print("\n" + "=" * 36)
    print("       LEGAL METROLOGY")
    print("=" * 36)

    print(
        "Overall status:",
        compliance_report["overall_status"],
    )

    print(
        "Mandatory declarations:",
        compliance_report[
            "mandatory_declarations_detected"
        ],
        "/",
        compliance_report[
            "mandatory_declarations_total"
        ],
    )

    for key, check in (
        compliance_report["checks"].items()
    ):
        print(
            f"{key:<35} "
            f"{check['status']}"
        )

    # --------------------------------------------------------
    # STRUCTURED RESULT
    # --------------------------------------------------------

    structured_result = build_structured_result(
        file_path=file_path,
        nutrition=nutrition,
        ingredients=ingredients,
        contains=contains,
        may_contain=may_contain,
        compliance_report=compliance_report,
        nutrients_total=len(NUTRIENTS),
    )

    save_json_result(
        structured_result,
        file_path,
        config["output_dir"],
    )

    # --------------------------------------------------------
    # DEBUG IMAGES
    # --------------------------------------------------------

    normalized_regions = normalize_regions(
        regions
    )

    save_debug_images(
        processed_color,
        normalized_regions,
        rois,
        file_path,
        config["output_dir"],
    )

    return {
        "image": image,
        "processed_color": processed_color,
        "processed_gray": processed_gray,
        "regions": normalized_regions,
        "rois": rois,
        "structured_result": structured_result,
    }


# ============================================================
# GUI
# ============================================================

def show_gui(result, config=CONFIG):

    if not config["show_gui"]:
        return

    if result is None:
        return

    processed = result["processed_color"]
    regions = result["regions"]
    rois = result["rois"]

    preview = draw_regions(
        processed,
        regions,
    )

    display = cv2.resize(
        preview,
        None,
        fx=0.20,
        fy=0.20,
    )

    cv2.imshow(
        "Detected Food Label Sections",
        display,
    )

    for name, roi in rois.items():

        if roi is None:
            continue

        display_roi = cv2.resize(
            roi,
            None,
            fx=0.35,
            fy=0.35,
        )

        cv2.imshow(
            f"{name.title()} ROI",
            display_roi,
        )

    print(
        "\nPress any key inside an OpenCV window "
        "to close the program."
    )

    cv2.waitKey(0)
    cv2.destroyAllWindows()


# ============================================================
# ENTRY POINT
# ============================================================

def main():

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = select_image()

    if not file_path:
        print("No image selected.")
        return

    try:
        result = process_image(
            file_path,
            CONFIG,
        )

        show_gui(
            result,
            CONFIG,
        )

    except Exception as exc:

        print(
            "\nERROR:",
            type(exc).__name__,
            str(exc),
        )

        raise


if __name__ == "__main__":
    main()
