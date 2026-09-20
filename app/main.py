"""
Application entry point for the packaged-food label analyzer.

This file is intentionally thin. It orchestrates the individual
OCR, region detection, compliance, food-analysis, and reporting
modules.
"""
import sys
from pathlib import Path

import cv2
from src.image_quality.quality import assess_image_quality

# GUI dependencies are loaded lazily.
# The FastAPI server does not need Tkinter.
tk = None
filedialog = None
messagebox = None
Image = None
ImageTk = None


def _load_gui_dependencies():
    global tk
    global filedialog
    global messagebox
    global Image
    global ImageTk

    if tk is not None:
        return

    import tkinter as _tk
    from tkinter import filedialog as _filedialog
    from tkinter import messagebox as _messagebox
    from PIL import Image as _Image
    from PIL import ImageTk as _ImageTk

    tk = _tk
    filedialog = _filedialog
    messagebox = _messagebox
    Image = _Image
    ImageTk = _ImageTk

from src.ocr.preprocessing import preprocess_image
from src.product_intelligence import identify_product
from src.ocr.engine import (
    build_ocr_summary,
    run_ocr,
    ocr_roi,
    extract_text_from_region,
)

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
    parse_nutrition_text,
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
        # OCR
    "ocr_engine": "paddle",
}


# ============================================================
# IMAGE SELECTION
# ============================================================

def select_image():
    _load_gui_dependencies()
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
    ocr_summary = build_ocr_summary(
        None,
        config.get("ocr_engine", "tesseract"),
    )
        # --------------------------------------------------------
    # IMAGE QUALITY
    # --------------------------------------------------------

    print("\nAssessing image quality...")

    image_quality = assess_image_quality(image)

    print(
        "Image quality score:",
        image_quality["score"],
    )

    print(
        "Image quality accepted:",
        image_quality["accepted"],
    )

    if not image_quality["accepted"]:
        print("\nImage quality check failed:")

        for reason in image_quality["rejection_reasons"]:
            print("-", reason)

        return {
            "image": image,
            "processed_color": None,
            "processed_gray": None,
            "regions": {},
            "rois": {},
            "structured_result": {
                "source_image": file_path,
                "ocr": ocr_summary,
                "image_quality": image_quality,
                "legal_metrology_compliance": {
                    "overall_status": "REVIEW",
                    "checks": {},
                    "mandatory_declarations_detected": 0,
                    "mandatory_declarations_total": 0,
                    "mandatory_declarations_review": 0,
                    "mandatory_declarations_missing": 0,
                    "disclaimer": (
                        "Image quality was insufficient "
                        "for reliable automated inspection."
                    ),
                },
            },
        }

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
        image_path=file_path,
        coordinate_scale=config["scale"],
    )

    ocr_summary = build_ocr_summary(
        data,
        engine_name=config.get("ocr_engine", "tesseract"),
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
    # --------------------------------------------------------
    # SECTION OCR
    # --------------------------------------------------------

    print("\nReading detected sections...")

    engine_name = str(
        config.get(
            "ocr_engine",
            "tesseract",
        )
    ).lower().strip()

    if engine_name == "paddle":

        # Reuse the single global PaddleOCR result.
        # Do not run PaddleOCR again for every ROI.

        nutrition_text = extract_text_from_region(
            data,
            nutrition_region,
        )

        ingredients_text = extract_text_from_region(
            data,
            ingredients_region,
        )

        allergen_text = extract_text_from_region(
            data,
            allergen_region,
        )

        if compliance_region is not None:

            left_region, right_region = (
                split_region_horizontally(
                    compliance_region,
                    config["compliance_split_ratio"],
                )
            )

            compliance_left_text = (
                extract_text_from_region(
                    data,
                    left_region,
                )
            )

            compliance_right_text = (
                extract_text_from_region(
                    data,
                    right_region,
                )
            )

        else:

            compliance_left_text = ""
            compliance_right_text = ""

        compliance_text = (
            compliance_left_text
            + "\n"
            + compliance_right_text
        )

    else:

        # Preserve the existing Tesseract ROI behaviour.

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
    # --------------------------------------------------------
    # FOOD ANALYSIS
    # --------------------------------------------------------

    if engine_name == "paddle":

        nutrition = parse_nutrition_text(
            nutrition_text,
            ocr_data=data,
        )

    else:

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
        ocr_data=data,
    )


    # --------------------------------------------------------
    # PRODUCT IDENTITY
    # --------------------------------------------------------

    product_identity = identify_product(
        raw_text,
        ocr_data=data,
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
        "Verified:",
        compliance_report[
            "mandatory_declarations_detected"
        ],
        "/",
        compliance_report[
            "mandatory_declarations_total"
        ],
    )

    print(
        "Requires review:",
        compliance_report[
            "mandatory_declarations_review"
        ],
    )

    print(
        "Not detected:",
        compliance_report[
            "mandatory_declarations_missing"
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
        ocr_summary=ocr_summary,
        nutrition=nutrition,
        ingredients=ingredients,
        contains=contains,
        may_contain=may_contain,
        compliance_report=compliance_report,
        nutrients_total=len(NUTRIENTS),
    )

    structured_result["image_quality"] = image_quality
    structured_result["product_identity"] = (
        product_identity
    )

    structured_result["product_name"] = (
        product_identity.get(
            "product_name"
        )
    )

    structured_result["product_name_confidence"] = (
        product_identity.get(
            "product_name_confidence"
        )
    )

    structured_result["product_name_evidence"] = (
        product_identity.get(
            "product_name_evidence"
        )
    )

    structured_result["brand"] = (
        product_identity.get(
            "brand"
        )
    )

    structured_result["brand_confidence"] = (
        product_identity.get(
            "brand_confidence"
        )
    )

    structured_result["brand_evidence"] = (
        product_identity.get(
            "brand_evidence"
        )
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
# GUI APPLICATION
# ============================================================

class FoodLabelAnalyzerGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Food Label Analyzer")
        self.root.geometry("1100x750")

        self.selected_file = None
        self.preview_image = None
        self.result = None

        self.build_ui()

    def build_ui(self):

        title = tk.Label(
            self.root,
            text="FOOD LABEL ANALYZER",
            font=("Arial", 24, "bold"),
        )
        title.pack(pady=(25, 5))

        subtitle = tk.Label(
            self.root,
            text="Packaged-food label compliance screening",
            font=("Arial", 12),
        )
        subtitle.pack()

        controls = tk.Frame(self.root)
        controls.pack(pady=20)

        tk.Button(
            controls,
            text="Choose Image",
            command=self.choose_image,
            font=("Arial", 12, "bold"),
            padx=20,
            pady=8,
        ).pack(side="left", padx=10)

        self.analyze_button = tk.Button(
            controls,
            text="Analyze Label",
            command=self.analyze,
            font=("Arial", 12, "bold"),
            padx=20,
            pady=8,
            state="disabled",
        )
        self.analyze_button.pack(side="left", padx=10)

        self.status = tk.Label(
            self.root,
            text="No image selected",
            font=("Arial", 11),
        )
        self.status.pack()

        main_frame = tk.Frame(self.root)
        main_frame.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=20,
        )

        image_frame = tk.LabelFrame(
            main_frame,
            text="Product Image",
            padx=10,
            pady=10,
        )
        image_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10),
        )

        self.image_label = tk.Label(
            image_frame,
            text="Choose an image",
            font=("Arial", 14),
        )
        self.image_label.pack(
            fill="both",
            expand=True,
        )

        result_frame = tk.LabelFrame(
            main_frame,
            text="Analysis Results",
            padx=10,
            pady=10,
        )
        result_frame.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(10, 0),
        )

        self.results = tk.Text(
            result_frame,
            wrap="word",
            font=("Arial", 11),
        )
        self.results.pack(
            fill="both",
            expand=True,
        )

    def choose_image(self):

        file_path = filedialog.askopenfilename(
            title="Select Food Label Image",
            filetypes=[
                (
                    "Image files",
                    "*.jpg *.jpeg *.png *.webp *.JPG *.JPEG *.PNG *.WEBP",
                ),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        self.selected_file = file_path

        self.status.config(
            text=f"Selected: {Path(file_path).name}"
        )

        self.analyze_button.config(
            state="normal"
        )

        try:
            image = Image.open(file_path)

            image.thumbnail((450, 500))

            self.preview_image = ImageTk.PhotoImage(image)

            self.image_label.config(
                image=self.preview_image,
                text="",
            )

        except Exception as exc:

            messagebox.showerror(
                "Image Error",
                str(exc),
            )

    def analyze(self):

        if not self.selected_file:
            return

        self.status.config(
            text="Analyzing..."
        )

        self.root.update_idletasks()

        try:

            self.result = process_image(
                self.selected_file,
                CONFIG,
            )

            self.show_results()

            self.status.config(
                text="Analysis complete",
            )

        except Exception as exc:

            self.status.config(
                text="Analysis failed",
            )

            messagebox.showerror(
                "Analysis Error",
                f"{type(exc).__name__}: {exc}",
            )

        finally:

            self.analyze_button.config(
                state="normal"
            )

    def show_results(self):

        structured = self.result[
            "structured_result"
        ]

        compliance = structured.get(
            "legal_metrology_compliance",
            {},
        )

        checks = compliance.get(
            "checks",
            {},
        )

        detected = compliance.get(
            "mandatory_declarations_detected",
            0,
        )

        total = compliance.get(
            "mandatory_declarations_total",
            0,
        )

        output = []

        output.append(
            "LEGAL METROLOGY COMPLIANCE"
        )

        output.append(
            "=" * 35
        )

        output.append(
            f"Mandatory declarations: {detected}/{total}"
        )

        output.append("")

        for key, check in checks.items():

            label = check.get(
                "label",
                key,
            )

            status = check.get(
                "status",
                "REVIEW",
            )

            output.append(
                f"{label}: {status}"
            )

        output.append("")
        output.append(
            "FOOD ANALYSIS"
        )

        output.append(
            "=" * 35
        )

        ingredients = structured.get(
            "ingredients",
            [],
        )

        output.append(
            "\nIngredients:"
        )

        if ingredients:

            for ingredient in ingredients:
                output.append(
                    f"• {ingredient}"
                )

        else:

            output.append(
                "No reliable ingredients detected."
            )

        allergens = structured.get(
            "allergens",
            {},
        )

        output.append("\nAllergens:")

        output.append(
            "Contains: "
            + ", ".join(
                allergens.get("contains", [])
            )
            if allergens.get("contains")
            else "Contains: None detected"
        )

        output.append(
            "May contain: "
            + ", ".join(
                allergens.get("may_contain", [])
            )
            if allergens.get("may_contain")
            else "May contain: None detected"
        )

        nutrition = structured.get(
            "nutrition",
            {},
        )

        output.append("\nNutrition:")

        if nutrition:

            for nutrient, value in nutrition.items():

                output.append(
                    f"• {nutrient}: "
                    f"{value.get('value')} "
                    f"{value.get('unit', '')}"
                )

        else:

            output.append(
                "No reliable nutrition values detected."
            )

        output.append("")
        output.append(
            "NOTE: Automated OCR-based first-pass "
            "screening. Not legal certification."
        )

        self.results.delete(
            "1.0",
            tk.END,
        )

        self.results.insert(
            tk.END,
            "\n".join(output),
        )


# ============================================================
# ENTRY POINT
# ============================================================

def main():

    # CLI mode
    #
    # python3 -m app.main images/IMG_0981.jpeg

    if len(sys.argv) > 1:

        file_path = sys.argv[1]

        process_image(
            file_path,
            CONFIG,
        )

        return

    # GUI mode
    #
    # python3 -m app.main

    _load_gui_dependencies()

    root = tk.Tk()

    FoodLabelAnalyzerGUI(
        root
    )

    root.mainloop()

if __name__ == "__main__":
    main()
