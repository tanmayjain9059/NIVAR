"""
analyzer.py

Image-based packaged-food label analyzer.

Two layers of output:
  1. LEGAL METROLOGY COMPLIANCE CHECK (primary, for SIH PS 34)
     - Checks OCR text against the mandatory declarations in
       Rule 6 of the Legal Metrology (Packaged Commodities)
       Rules, 2011. This is an automated first-pass heuristic,
       NOT a legal compliance certification.

  2. NUTRITION / INGREDIENTS / ALLERGENS (secondary, strengthens
     the idea beyond the bare legal checklist)

Run with:
    python analyzer.py
(opens a file picker) or:
    python analyzer.py /path/to/image.jpg
"""

import sys
import json
import re
from pathlib import Path

import cv2
import pytesseract


# ============================================================
# CONFIG
#
# Every tunable threshold lives here. If region detection is
# too loose/tight, or a compliance regex misses real labels,
# change it here — not buried inside a function.
# ============================================================

CONFIG = {
    # --- preprocessing ---
    "scale": 1.5,
    "global_ocr_config": "--psm 11",
    "roi_ocr_config": "--psm 6",
    "roi_denoise_kernel": 3,  # must be odd; median blur kernel before Otsu binarization
    "polarity_dark_threshold": 128,  # mean gray value below which the image is inverted for OCR

    # --- nutrition region detection ---
    "nutrition_row_gap_max": 500,
    "nutrition_min_rows_in_group": 3,
    "nutrition_heading_search_up": 900,
    "nutrition_heading_offset": 120,
    "nutrition_no_heading_offset": 180,
    "nutrition_bottom_padding": 300,
    "nutrition_bottom_hard_max": 2200,
    "nutrition_left_padding": 600,
    "nutrition_right_padding": 1000,

    # --- ingredients region detection ---
    "ingredients_heading_offset": 100,
    "ingredients_max_height": 1500,
    "ingredients_horizontal_window": 1100,
    "ingredients_left_padding": 100,
    "ingredients_right_padding": 150,
    "ingredients_bottom_padding": 100,

    # --- allergen region detection ---
    "allergen_heading_offset": 100,
    "allergen_max_height": 900,
    "allergen_horizontal_window": 1000,
    "allergen_left_padding": 100,
    "allergen_right_padding": 150,
    "allergen_bottom_padding": 100,

    # --- compliance region detection ---
    "compliance_top_padding": 100,
    # Heuristic fixed split for the two-column layout (address block
    # left, MRP/dates right) seen in this label. Not dynamically
    # detected yet — if this doesn't generalize to other packages,
    # replace with a gap-detection split based on word x-positions.
    "compliance_column_split_ratio": 0.42,

    # --- nutrient value matching ---
    "nutrient_vertical_tolerance": 120,
    "nutrient_horizontal_max": 1000,
    "nutrient_score_threshold": 700,

    # --- output ---
    "output_dir": "results",
    "save_debug_images": True,
    "show_gui": True,
}

NUTRIENTS = [
    "Energy",
    "Protein",
    "Carbohydrate",
    "Total Sugars",
    "Added Sugars",
    "Dietary Fiber",
    "Total Fat",
    "Saturated Fat",
    "Trans Fat",
    "Cholesterol",
    "Sodium",
]


# ============================================================
# SECTION 1 — IMAGE INPUT
# ============================================================

def select_image_via_dialog():
    """Opens a file picker. Returns a path string, or None."""

    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select Food Package Image",
        filetypes=[
            ("Image files", "*.jpg *.jpeg *.png *.webp"),
            ("All files", "*.*"),
        ],
    )

    root.destroy()

    return file_path or None


def load_image(file_path):

    image = cv2.imread(str(file_path))

    if image is None:
        print(f"Could not load image: {file_path}")
        return None

    return image


# ============================================================
# SECTION 2 — PREPROCESSING
# ============================================================

def normalize_polarity(gray, config=CONFIG):
    """
    Tesseract's recognition models are trained mostly on ordinary
    dark-text-on-light-background print. Many Indian packaged-food
    labels (including this one) use light/white text on a dark
    background ("reversed video"), which degrades OCR accuracy
    badly even when the image looks perfectly legible to a human.

    Confirmed on a real test image: the nutrition-table crop was
    clearly readable by eye (light text on near-black background)
    but Tesseract read it as near-total garbage. Inverting
    dark-background images before OCR is the standard fix for
    this failure mode.

    Heuristic: if the image is predominantly dark (mean pixel
    value below the threshold), invert it. Package photos with a
    normal light background and dark text are left unchanged.
    """

    if gray.mean() < config["polarity_dark_threshold"]:
        print("Detected dark-background label — inverting for OCR.")
        return cv2.bitwise_not(gray)

    return gray


def preprocess_image(image, config=CONFIG):

    scale = config["scale"]

    enlarged = cv2.resize(
        image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
    )
    print(f"Image enlarged by {scale}x")

    gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    print("Contrast enhancement complete.")

    enhanced = normalize_polarity(enhanced, config)

    return enlarged, enhanced


# ============================================================
# SECTION 3 — OCR
# ============================================================

def run_ocr(image, config=CONFIG):

    print("Running OCR...")

    data = pytesseract.image_to_data(
        image,
        config=config["global_ocr_config"],
        output_type=pytesseract.Output.DATAFRAME,
    )

    data = data.dropna(subset=["text"])
    data["text"] = data["text"].astype(str).str.strip()
    data = data[data["text"] != ""].copy()

    for col in ("left", "top", "width", "height"):
        data[col] = data[col].astype(int)

    data["right"] = data["left"] + data["width"]
    data["bottom"] = data["top"] + data["height"]

    text = pytesseract.image_to_string(image, config=config["global_ocr_config"])

    print("OCR complete.")

    return data, text


def prepare_roi_for_ocr(roi, config=CONFIG):
    """
    Cleans a cropped region specifically for OCR: denoises the
    grain visible in these camera-shot crops, then binarizes with
    Otsu thresholding. CLAHE + polarity inversion (applied to the
    whole page) were not enough on their own — confirmed by crops
    that look clean to a human eye still producing garbled
    Tesseract output. Denoising + true black/white binarization is
    the standard next step for this failure mode.
    """

    if roi is None:
        return None

    denoised = cv2.medianBlur(roi, config["roi_denoise_kernel"])

    _, binarized = cv2.threshold(
        denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return binarized


def ocr_roi(roi, config=CONFIG):

    if roi is None:
        return ""

    cleaned = prepare_roi_for_ocr(roi, config)

    return pytesseract.image_to_string(cleaned, config=config["roi_ocr_config"])


def clean_word(text):

    return re.sub(r"[^a-z0-9]", "", str(text).lower())


# ============================================================
# SECTION 4 — REGION DETECTION
#
# Confirmed working on one test image (IMG_0981.jpeg). Not yet
# validated across different layouts/resolutions — treat
# detection failures as expected until tested more broadly.
# ============================================================

def find_ingredients_heading(data):

    matches = [row for _, row in data.iterrows() if "ingredient" in clean_word(row["text"])]

    if not matches:
        return None

    matches.sort(key=lambda row: row["top"])
    row = matches[0]

    return {
        "x": int(row["left"]),
        "y": int(row["top"]),
        "right": int(row["right"]),
        "bottom": int(row["bottom"]),
    }


def detect_nutrition_region(image, data, config=CONFIG):

    height, width = image.shape[:2]

    keywords = ["energy", "protein", "carbohydrate", "sugars", "fat", "cholesterol", "sodium"]

    nutrition_rows = []

    for _, row in data.iterrows():
        word = clean_word(row["text"])
        if not word:
            continue
        if any(k in word for k in keywords):
            nutrition_rows.append({
                "x": int(row["left"]), "y": int(row["top"]),
                "right": int(row["right"]), "bottom": int(row["bottom"]),
            })

    if len(nutrition_rows) < config["nutrition_min_rows_in_group"]:
        return None

    nutrition_rows.sort(key=lambda item: item["y"])

    groups = []
    current_group = [nutrition_rows[0]]

    for row in nutrition_rows[1:]:
        previous = current_group[-1]
        gap = row["y"] - previous["bottom"]

        if gap <= config["nutrition_row_gap_max"]:
            current_group.append(row)
        else:
            if len(current_group) >= config["nutrition_min_rows_in_group"]:
                groups.append(current_group)
            current_group = [row]

    if len(current_group) >= config["nutrition_min_rows_in_group"]:
        groups.append(current_group)

    if not groups:
        return None

    best_group = max(groups, key=len)

    min_x = min(r["x"] for r in best_group)
    max_x = max(r["right"] for r in best_group)
    first_y = min(r["y"] for r in best_group)
    last_y = max(r["bottom"] for r in best_group)

    heading_y = None
    for _, row in data.iterrows():
        word = clean_word(row["text"])
        if "nutrition" in word or "nutritional" in word:
            y = int(row["top"])
            if y < first_y and first_y - y < config["nutrition_heading_search_up"]:
                if heading_y is None or y > heading_y:
                    heading_y = y

    if heading_y is not None:
        top = heading_y - config["nutrition_heading_offset"]
    else:
        top = first_y - config["nutrition_no_heading_offset"]

    bottom = last_y + config["nutrition_bottom_padding"]
    bottom = min(bottom, first_y + config["nutrition_bottom_hard_max"])

    left = max(0, min_x - config["nutrition_left_padding"])
    right = min(width, max_x + config["nutrition_right_padding"])
    top = max(0, top)
    bottom = min(height, bottom)

    if right <= left or bottom <= top:
        return None

    return {"x1": left, "y1": top, "x2": right, "y2": bottom}


def detect_ingredients_region(image, data, nutrition_region, config=CONFIG):

    height, width = image.shape[:2]

    heading = find_ingredients_heading(data)
    if heading is None:
        return None

    start_y = heading["y"] - config["ingredients_heading_offset"]

    if nutrition_region is not None:
        nutrition_top = nutrition_region["y1"]
        if nutrition_top > start_y:
            end_y = nutrition_top - 30
        else:
            end_y = min(height, start_y + config["ingredients_max_height"])
    else:
        end_y = min(height, start_y + config["ingredients_max_height"])

    heading_center_x = (heading["x"] + heading["right"]) / 2
    words = []

    for _, row in data.iterrows():
        x, y = int(row["left"]), int(row["top"])
        right, bottom = int(row["right"]), int(row["bottom"])

        if y < start_y or y > end_y:
            continue

        center_x = (x + right) / 2
        if abs(center_x - heading_center_x) > config["ingredients_horizontal_window"]:
            continue

        words.append((x, y, right, bottom))

    if not words:
        return None

    min_x = min(w[0] for w in words)
    max_x = max(w[2] for w in words)
    max_y = max(w[3] for w in words)

    return {
        "x1": max(0, min_x - config["ingredients_left_padding"]),
        "y1": max(0, start_y),
        "x2": min(width, max_x + config["ingredients_right_padding"]),
        "y2": min(height, max_y + config["ingredients_bottom_padding"]),
    }


def detect_allergen_region(image, data, config=CONFIG):

    height, width = image.shape[:2]
    matches = [row for _, row in data.iterrows() if "allergen" in clean_word(row["text"])]

    if not matches:
        rows = list(data.sort_values(["top", "left"]).itertuples())

        for i, row in enumerate(rows):
            word = clean_word(row.text)
            if word not in ("may", "contains", "contain"):
                continue

            nearby = "".join(clean_word(rows[j].text) for j in range(max(0, i - 1), min(len(rows), i + 3)))

            if "maycontain" in nearby:
                matches.append(row)
                break

    if not matches:
        return None

    matches.sort(key=lambda row: row["top"])
    heading = matches[0]

    start_y = int(heading["top"]) - config["allergen_heading_offset"]
    center_x = int(heading["left"]) + int(heading["width"]) / 2

    words = []
    for _, row in data.iterrows():
        x, y = int(row["left"]), int(row["top"])
        right, bottom = int(row["right"]), int(row["bottom"])

        if y < start_y or y > start_y + config["allergen_max_height"]:
            continue

        word_center = (x + right) / 2
        if abs(word_center - center_x) > config["allergen_horizontal_window"]:
            continue

        words.append((x, y, right, bottom))

    if not words:
        return None

    min_x = min(w[0] for w in words)
    max_x = max(w[2] for w in words)
    max_y = max(w[3] for w in words)

    return {
        "x1": max(0, min_x - config["allergen_left_padding"]),
        "y1": max(0, start_y),
        "x2": min(width, max_x + config["allergen_right_padding"]),
        "y2": min(height, max_y + config["allergen_bottom_padding"]),
    }


def crop_region(image, region):

    if region is None:
        return None

    return image[region["y1"]:region["y2"], region["x1"]:region["x2"]]


# ------------------------------------------------------------
# Compliance region detection
#
# Applies the same detect -> crop -> re-OCR pattern used for
# nutrition/ingredients/allergens to the Legal Metrology
# declarations block. Previously this ran regex directly against
# the noisy full-page OCR text, which is far less reliable than
# a focused crop — confirmed by the nutrition table failing the
# same way until it got this treatment.
# ------------------------------------------------------------

def find_compliance_heading(data):
    """
    Finds the earliest "Manufactured by / Marketed by / Packed by"
    style heading. On Indian packaging this heading reliably marks
    the start of the block that also contains MRP, packing/expiry
    dates, and consumer-care details.
    """

    heading_keywords = ["manufactured", "marketed", "packedby", "importedby", "packer"]

    matches = []

    for _, row in data.iterrows():
        word = clean_word(row["text"])
        if any(k in word for k in heading_keywords):
            matches.append(row)

    if not matches:
        return None

    matches.sort(key=lambda row: row["top"])
    row = matches[0]

    return {
        "x": int(row["left"]), "y": int(row["top"]),
        "right": int(row["right"]), "bottom": int(row["bottom"]),
    }


def detect_compliance_region(image, data, config=CONFIG):
    """
    Region spanning from the manufacturer/marketer heading down to
    the bottom of the image, full width. This block (MRP, dates,
    consumer care) is typically the last major printed content on
    the label, so a fixed "heading to bottom" span is a reasonable
    first heuristic — not validated across multiple package layouts
    yet, so treat detection failures as expected until tested more
    broadly.
    """

    height, width = image.shape[:2]

    heading = find_compliance_heading(data)
    if heading is None:
        return None

    top = max(0, heading["y"] - config["compliance_top_padding"])

    return {"x1": 0, "y1": top, "x2": width, "y2": height}


def split_region_horizontally(region, ratio):
    """
    Splits a region into left/right halves at the given ratio of
    its width. Used for the compliance block, which is a genuine
    two-column layout — confirmed by --psm 6 output that interleaved
    sentences from both columns mid-word. OCRing each column
    separately avoids that collapse.
    """

    if region is None:
        return None, None

    width = region["x2"] - region["x1"]
    split_x = region["x1"] + int(width * ratio)

    left = {"x1": region["x1"], "y1": region["y1"], "x2": split_x, "y2": region["y2"]}
    right = {"x1": split_x, "y1": region["y1"], "x2": region["x2"], "y2": region["y2"]}

    return left, right





# ============================================================
# SECTION 5 — SECTION PARSING
# ============================================================

def parse_nutrition_table(roi, config=CONFIG):
    """
    Runs a focused OCR pass on the cropped nutrition-table region
    and parses it. Denoise + binarize first (see
    prepare_roi_for_ocr) — a clean-looking crop still OCR'd badly
    without this step.
    """

    if roi is None:
        return {}

    cleaned = prepare_roi_for_ocr(roi, config)

    data = pytesseract.image_to_data(
        cleaned, config=config["roi_ocr_config"], output_type=pytesseract.Output.DATAFRAME
    )
    data = data.dropna(subset=["text"])
    data["text"] = data["text"].astype(str).str.strip()
    data = data[data["text"] != ""].copy()

    for col in ("left", "top", "width", "height"):
        data[col] = data[col].astype(int)

    number_tokens = []
    for _, row in data.iterrows():
        for number in re.findall(r"\d+(?:\.\d+)?", str(row["text"])):
            try:
                value = float(number)
            except ValueError:
                continue
            number_tokens.append({
                "value": value, "x": int(row["left"]), "y": int(row["top"]),
                "right": int(row["left"]) + int(row["width"]),
                "bottom": int(row["top"]) + int(row["height"]),
            })

    results = {}

    for nutrient in NUTRIENTS:
        target = re.sub(r"[^a-z]", "", nutrient.lower())
        matches = [row for _, row in data.iterrows() if target in re.sub(r"[^a-z]", "", str(row["text"]).lower())]

        if not matches:
            continue

        nutrient_row = matches[0]
        nutrient_y = int(nutrient_row["top"])
        nutrient_right = int(nutrient_row["left"]) + int(nutrient_row["width"])

        candidates = []
        for number in number_tokens:
            vertical_distance = abs(number["y"] - nutrient_y)
            if vertical_distance > config["nutrient_vertical_tolerance"]:
                continue
            if number["x"] <= nutrient_right:
                continue
            horizontal_distance = number["x"] - nutrient_right
            if horizontal_distance > config["nutrient_horizontal_max"]:
                continue

            score = vertical_distance * 3 + horizontal_distance
            candidates.append({"value": number["value"], "score": score})

        if not candidates:
            continue

        candidates.sort(key=lambda item: item["score"])
        best = candidates[0]

        if best["score"] > config["nutrient_score_threshold"]:
            continue

        if nutrient == "Energy":
            unit = "kcal"
        elif nutrient in ("Sodium", "Cholesterol"):
            unit = "mg"
        else:
            unit = "g"

        results[nutrient] = {"value": best["value"], "unit": unit}

    return results


def parse_ingredients(text):

    if not text:
        return []

    text = re.sub(r"^\s*INGREDIENTS?\s*:?", "", text, flags=re.IGNORECASE)
    text = " ".join(text.split())

    for phrase in ("Nutritional Information", "Nutrition Information", "Allergen:", "Allergens:"):
        index = text.lower().find(phrase.lower())
        if index != -1:
            text = text[:index]

    ingredients = []
    current = ""
    parentheses = 0

    for char in text:
        if char == "(":
            parentheses += 1
        elif char == ")":
            parentheses = max(0, parentheses - 1)

        if char == "," and parentheses == 0:
            if current.strip():
                ingredients.append(current.strip())
            current = ""
        else:
            current += char

    if current.strip():
        ingredients.append(current.strip())

    garbage_phrases = ["made from", "chocolate indulgence", "store in", "manufactured by"]
    cleaned = []

    for ingredient in ingredients:
        ingredient = ingredient.strip().rstrip(".,;")
        if len(ingredient) < 2:
            continue
        if any(g in ingredient.lower() for g in garbage_phrases):
            continue
        cleaned.append(ingredient)

    return cleaned


def parse_allergens(text):

    contains, may_contain = [], []

    if not text:
        return contains, may_contain

    text = " ".join(text.split())

    match = re.search(r"Contains\s+(.+?)(?=May Contains|$)", text, flags=re.IGNORECASE)
    if match:
        value = match.group(1).replace(" & ", ", ")
        contains = [item.strip().rstrip(".") for item in value.split(",") if item.strip()]

    match = re.search(r"May Contains\s+(.+)$", text, flags=re.IGNORECASE)
    if match:
        value = match.group(1).replace(" & ", ", ")
        may_contain = [item.strip().rstrip(".") for item in value.split(",") if item.strip()]

    return contains, may_contain


# ============================================================
# SECTION 6 — LEGAL METROLOGY COMPLIANCE CHECK
# (Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6)
#
# This is an automated OCR-based first-pass check, NOT a legal
# compliance certification. "NOT DETECTED" does not prove a
# declaration is absent from the physical package.
# ============================================================

def check_legal_metrology_compliance(raw_text, compliance_text=None):
    """
    raw_text: full-page global OCR text (fallback / still used for
              net_quantity and mrp, which were already reliable
              here).
    compliance_text: focused OCR of the detected compliance region
              (see detect_compliance_region) — checked first when
              available, since it's a cleaner read of the same
              content. Falls back to raw_text alone when no
              compliance region was detected.
    """

    # Search the focused crop first (if we have one), then the
    # full page — re.search returns the leftmost match, so this
    # naturally prefers the cleaner source without discarding the
    # fallback.
    text = f"{compliance_text}\n{raw_text}" if compliance_text else (raw_text or "")

    checks = {}

    pattern = re.search(r"(manufactured|packed|marketed|imported)\s+by", text, re.IGNORECASE)
    checks["manufacturer_packer_importer"] = {
        "label": "Name & address of manufacturer/packer/importer",
        "detected": bool(pattern),
        "matched_text": pattern.group(0) if pattern else None,
    }

    pattern = re.search(
        r"\b\d+(\.\d+)?\s*(g|gm|gms|kg|ml|l|litre|liter|ltr|pcs|pieces|n\b)", text, re.IGNORECASE
    )
    checks["net_quantity"] = {
        "label": "Net quantity (weight/volume/number)",
        "detected": bool(pattern),
        "matched_text": pattern.group(0) if pattern else None,
    }

    # Supports DD/MM/YYYY, DD/MonthName/YY(YY) (e.g. "Pkd.25/JUN/26"),
    # and "Month YYYY".
    pattern = re.search(
        r"(mfg|mfd|pkd|packed on|manufactured on)\D{0,10}"
        r"(\d{1,2}[/\-][a-z]{3,9}[/\-]\d{2,4}"
        r"|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}"
        r"|[a-z]{3,9}\s*\d{4})",
        text, re.IGNORECASE,
    )
    checks["manufacture_date"] = {
        "label": "Month & year of manufacture/packing",
        "detected": bool(pattern),
        "matched_text": pattern.group(0) if pattern else None,
    }

    pattern = re.search(r"(mrp|m\.r\.p|retail sale price)\D{0,10}\d+(\.\d+)?", text, re.IGNORECASE)
    checks["mrp"] = {
        "label": "Retail Sale Price (MRP), inclusive of taxes",
        "detected": bool(pattern),
        "matched_text": pattern.group(0) if pattern else None,
    }

    email_pattern = re.search(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", text, re.IGNORECASE)
    # Phone numbers on Indian packaging are often printed as
    # space/dash-separated groups (e.g. "1800 258 3333"), not one
    # contiguous digit run — match digit groups joined by spaces/dashes.
    phone_pattern = re.search(
        r"(consumer|customer)\s*care.{0,60}?(\d[\d\s\-]{7,}\d)",
        text, re.IGNORECASE | re.DOTALL,
    )
    checks["consumer_care"] = {
        "label": "Consumer care details (contact for complaints)",
        "detected": bool(email_pattern or phone_pattern),
        "matched_text": (email_pattern.group(0) if email_pattern
                          else (phone_pattern.group(0) if phone_pattern else None)),
    }

    pattern = re.search(r"(country of origin|made in)\D{0,20}[a-z]+", text, re.IGNORECASE)
    checks["country_of_origin"] = {
        "label": "Country of origin (mandatory only for imported goods)",
        "detected": bool(pattern),
        "matched_text": pattern.group(0) if pattern else None,
        "conditional": True,
    }

    checks["generic_name"] = {
        "label": "Generic/common name of the commodity",
        "detected": None,
        "matched_text": None,
        "note": "Requires product-name extraction; not yet implemented.",
    }

    mandatory_keys = [
        "manufacturer_packer_importer", "net_quantity", "manufacture_date", "mrp", "consumer_care",
    ]
    detected_count = sum(1 for k in mandatory_keys if checks[k]["detected"])

    return {
        "checks": checks,
        "mandatory_declarations_detected": detected_count,
        "mandatory_declarations_total": len(mandatory_keys),
        "disclaimer": (
            "Automated OCR-based check. NOT DETECTED does not confirm "
            "absence on the physical package. Verify manually before "
            "any compliance claim."
        ),
    }


# ============================================================
# SECTION 7 — STRUCTURED OUTPUT
# ============================================================

def build_structured_result(file_path, nutrition, ingredients, contains, may_contain, compliance_report):

    return {
        "source_image": str(file_path),
        "legal_metrology_compliance": compliance_report,
        "brand": None,
        "product_name": None,
        "ingredients": ingredients,
        "allergens": {"contains": contains, "may_contain": may_contain},
        "nutrition": {
            nutrient: {"value": item["value"], "unit": item["unit"]}
            for nutrient, item in nutrition.items()
        },
        "quantity": None,
        "manufacturer": None,
        "manufacturing_date": None,
        "expiry_date": None,
        "meta": {
            "nutrition_fields_found": len(nutrition),
            "nutrition_fields_total": len(NUTRIENTS),
            "ingredients_found": len(ingredients),
            "confirmed_allergens": len(contains),
            "possible_allergens": len(may_contain),
        },
    }


def save_json_result(result, source_image_path, config=CONFIG):

    output_dir = Path(config["output_dir"])
    output_dir.mkdir(exist_ok=True)

    stem = Path(source_image_path).stem
    output_path = output_dir / f"{stem}_result.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nStructured result saved to: {output_path}")

    return output_path


def save_debug_images(processed, regions, rois, source_image_path, config=CONFIG):
    """
    Saves region-overlay + individual ROI crops to disk instead of
    (or in addition to) cv2.imshow, so results are inspectable
    without a GUI session — needed for a headless demo/test run.
    """

    if not config["save_debug_images"]:
        return

    debug_dir = Path(config["output_dir"]) / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(source_image_path).stem

    preview = draw_regions(processed, regions)
    cv2.imwrite(str(debug_dir / f"{stem}_regions.jpg"), preview)

    for name, roi in rois.items():
        if roi is not None:
            cv2.imwrite(str(debug_dir / f"{stem}_{name}_roi.jpg"), roi)

    print(f"Debug images saved to: {debug_dir}")


def draw_regions(image, regions):

    preview = image.copy()
    colors = {
        "ingredients": (0, 255, 0), "nutrition": (255, 0, 0),
        "allergens": (0, 0, 255), "compliance": (0, 255, 255),
    }

    for name, region in regions.items():
        if region is None:
            continue

        x1, y1, x2, y2 = region["x1"], region["y1"], region["x2"], region["y2"]
        cv2.rectangle(preview, (x1, y1), (x2, y2), colors[name], 8)
        cv2.putText(preview, name.upper(), (x1, max(50, y1 - 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, colors[name], 4)

    return preview


# ============================================================
# SECTION 8 — CONSOLE REPORTS
# ============================================================

def print_compliance_report(report):

    print("\n" + "=" * 50)
    print("   LEGAL METROLOGY COMPLIANCE CHECK")
    print("       (PC Rules 2011, Rule 6)")
    print("=" * 50)

    for item in report["checks"].values():
        if item["detected"] is None:
            status = "N/A - MANUAL REVIEW"
        elif item["detected"]:
            status = "DETECTED"
        else:
            status = "NOT DETECTED"

        print(f"\n{item['label']}")
        print(f"  Status: {status}")
        if item.get("matched_text"):
            print(f"  Matched: {item['matched_text']}")

    print(
        f"\nMandatory declarations detected: "
        f"{report['mandatory_declarations_detected']}/{report['mandatory_declarations_total']}"
    )
    print(f"\nNote: {report['disclaimer']}")
    print("=" * 50)


def print_results(nutrition, ingredients, contains, may_contain):

    print("\n" + "=" * 36)
    print("       STRUCTURED NUTRITION")
    print("=" * 36)

    if nutrition:
        for nutrient, item in nutrition.items():
            print(f"{nutrient:<18}: {item['value']} {item['unit']}")
    else:
        print("No reliable nutrition values found.")

    print("\n" + "=" * 36)
    print("       STRUCTURED INGREDIENTS")
    print("=" * 36)

    if ingredients:
        for i, ingredient in enumerate(ingredients, 1):
            print(f"{i}. {ingredient}")
    else:
        print("No reliable ingredients found.")

    print("\n" + "=" * 36)
    print("       STRUCTURED ALLERGENS")
    print("=" * 36)

    print("\nContains:")
    for item in contains or ["- None detected"]:
        print(f"- {item}" if contains else item)

    print("\nMay contain:")
    for item in may_contain or ["- None detected"]:
        print(f"- {item}" if may_contain else item)

    print("\n" + "=" * 36)
    print("        FOOD LABEL ANALYZER")
    print("=" * 36)
    print(f"\nNutrition values found: {len(nutrition)}/{len(NUTRIENTS)}")
    print(f"Ingredients found: {len(ingredients)}")
    print(f"Confirmed allergens: {len(contains)}")
    print(f"Possible allergens: {len(may_contain)}")
    print("\n" + "=" * 36)


# ============================================================
# SECTION 9 — PIPELINE ORCHESTRATION
#
# process_image() is the reusable core — call this directly
# from a future API/backend without touching any UI code.
# ============================================================

def process_image(file_path, config=CONFIG):

    image = load_image(file_path)
    if image is None:
        return None

    height, width, channels = image.shape
    print(f"\nImage loaded: {file_path}")
    print(f"Width: {width}  Height: {height}  Channels: {channels}")

    enlarged, processed = preprocess_image(image, config)
    ocr_data, raw_text = run_ocr(processed, config)

    print("\n========== RAW OCR TEXT ==========")
    print(raw_text)
    print("===================================")

    print("\nDetecting section regions...")
    nutrition_region = detect_nutrition_region(processed, ocr_data, config)
    ingredients_region = detect_ingredients_region(processed, ocr_data, nutrition_region, config)
    allergen_region = detect_allergen_region(processed, ocr_data, config)
    compliance_region = detect_compliance_region(processed, ocr_data, config)

    regions = {
        "ingredients": ingredients_region,
        "nutrition": nutrition_region,
        "allergens": allergen_region,
        "compliance": compliance_region,
    }

    print("\n========== DETECTED REGIONS ==========")
    for name, region in regions.items():
        if region is None:
            print(f"{name.title()}: Not detected")
        else:
            print(f"{name.title()}: ({region['x1']}, {region['y1']}) -> ({region['x2']}, {region['y2']})")
    print("=======================================")

    rois = {
        "nutrition": crop_region(processed, nutrition_region),
        "ingredients": crop_region(processed, ingredients_region),
        "allergens": crop_region(processed, allergen_region),
        "compliance": crop_region(processed, compliance_region),
    }

    # Compliance block is a genuine two-column layout — OCR each
    # column separately rather than as one block (see
    # split_region_horizontally) to avoid interleaving sentences
    # from both columns into garbage.
    compliance_left_region, compliance_right_region = split_region_horizontally(
        compliance_region, config["compliance_column_split_ratio"]
    )
    compliance_left_roi = crop_region(processed, compliance_left_region)
    compliance_right_roi = crop_region(processed, compliance_right_region)

    print("\nReading detected sections...")

    nutrition_text = ocr_roi(rois["nutrition"], config)
    ingredients_text = ocr_roi(rois["ingredients"], config)
    allergen_text = ocr_roi(rois["allergens"], config)
    compliance_left_text = ocr_roi(compliance_left_roi, config)
    compliance_right_text = ocr_roi(compliance_right_roi, config)
    compliance_text = compliance_left_text + "\n" + compliance_right_text

    print("\n" + "=" * 36)
    print("       SECTION OCR")
    print("=" * 36)
    print("\n--- NUTRITION ---\n" + nutrition_text)
    print("\n--- INGREDIENTS ---\n" + ingredients_text)
    print("\n--- ALLERGENS ---\n" + allergen_text)
    print("\n--- COMPLIANCE BLOCK (left column) ---\n" + compliance_left_text)
    print("\n--- COMPLIANCE BLOCK (right column) ---\n" + compliance_right_text)

    nutrition = parse_nutrition_table(rois["nutrition"], config)
    ingredients = parse_ingredients(ingredients_text)
    contains, may_contain = parse_allergens(allergen_text)

    compliance_report = check_legal_metrology_compliance(raw_text, compliance_text)
    print_compliance_report(compliance_report)

    print_results(nutrition, ingredients, contains, may_contain)

    structured_result = build_structured_result(
        file_path, nutrition, ingredients, contains, may_contain, compliance_report
    )
    save_json_result(structured_result, file_path, config)
    rois["compliance_left"] = compliance_left_roi
    rois["compliance_right"] = compliance_right_roi
    save_debug_images(processed, regions, rois, file_path, config)

    return {
        "processed_image": processed,
        "regions": regions,
        "rois": rois,
        "structured_result": structured_result,
    }


def show_gui(result, config=CONFIG):

    if not config["show_gui"] or result is None:
        return

    processed = result["processed_image"]
    regions = result["regions"]
    rois = result["rois"]

    preview = draw_regions(processed, regions)
    display = cv2.resize(preview, None, fx=0.20, fy=0.20)
    cv2.imshow("Detected Food Label Sections", display)

    for name, roi in rois.items():
        if roi is not None:
            cv2.imshow(f"{name.title()} ROI", cv2.resize(roi, None, fx=0.35, fy=0.35))

    print("\nPress any key inside an OpenCV window to close the program.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = select_image_via_dialog()

    if not file_path:
        print("No image selected.")
        return

    result = process_image(file_path)
    show_gui(result)


if __name__ == "__main__":
    main()