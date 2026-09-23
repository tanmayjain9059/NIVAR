"""
Reusable OCR evidence utilities for semantic declaration extraction.

These helpers deliberately use relative geometry and observed OCR text size
instead of fixed pixel distances, so declaration extraction can generalize
across image resolutions and package layouts.
"""

import math
import re


def normalize_text(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def _conf(value):
    try:
        value = float(value)
        return value / 100 if value > 1 else max(0.0, min(value, 1.0))
    except (TypeError, ValueError):
        return 0.0


def ocr_rows(ocr_data):
    if ocr_data is None or getattr(ocr_data, "empty", True):
        return []

    rows = []
    for index, row in ocr_data.iterrows():
        text = normalize_text(row.get("text"))
        if not text:
            continue
        try:
            left = float(row["left"])
            top = float(row["top"])
            right = float(row["right"])
            bottom = float(row["bottom"])
        except (KeyError, TypeError, ValueError):
            continue

        item = row.copy()
        item["_index"] = index
        item["_left"] = left
        item["_top"] = top
        item["_right"] = right
        item["_bottom"] = bottom
        item["_height"] = max(1.0, bottom - top)
        item["_width"] = max(1.0, right - left)
        item["_cx"] = (left + right) / 2.0
        item["_cy"] = (top + bottom) / 2.0
        rows.append(item)

    return rows


def median_text_height(rows):
    heights = sorted(r["_height"] for r in rows if r.get("_height"))
    if not heights:
        return 20.0
    middle = len(heights) // 2
    if len(heights) % 2:
        return heights[middle]
    return (heights[middle - 1] + heights[middle]) / 2.0


def build_line_groups(ocr_data):
    """Merge OCR boxes that belong to the same visual text line."""
    rows = ocr_rows(ocr_data)
    if not rows:
        return []

    tolerance = max(8.0, median_text_height(rows) * 0.65)
    groups = []

    for row in sorted(rows, key=lambda item: (item["_cy"], item["_left"])):
        target = None
        best_delta = None

        for group in groups:
            delta = abs(row["_cy"] - group["_cy"])
            if delta <= tolerance and (best_delta is None or delta < best_delta):
                target = group
                best_delta = delta

        if target is None:
            groups.append({"_cy": row["_cy"], "rows": [row]})
        else:
            target["rows"].append(row)
            target["_cy"] = sum(item["_cy"] for item in target["rows"]) / len(target["rows"])

    output = []
    for group in sorted(groups, key=lambda item: min(row["_top"] for row in item["rows"])):
        members = sorted(group["rows"], key=lambda item: item["_left"])
        output.append(
            {
                "text": normalize_text(" ".join(normalize_text(row.get("text")) for row in members)),
                "rows": members,
                "left": min(row["_left"] for row in members),
                "top": min(row["_top"] for row in members),
                "right": max(row["_right"] for row in members),
                "bottom": max(row["_bottom"] for row in members),
                "confidence": sum(_conf(row.get("conf", 0)) for row in members) / len(members),
            }
        )

    return output


def grouped_text(ocr_data):
    groups = build_line_groups(ocr_data)
    return "\n".join(group["text"] for group in groups if group["text"])


def row_evidence(row, text=None):
    try:
        return {
            "text": normalize_text(text if text is not None else row.get("text")),
            "confidence": _conf(row.get("conf", 0)),
            "bbox": {
                "x1": int(row["_left"]),
                "y1": int(row["_top"]),
                "x2": int(row["_right"]),
                "y2": int(row["_bottom"]),
            },
        }
    except (KeyError, TypeError, ValueError):
        return None


def group_evidence(group):
    return {
        "text": group["text"],
        "confidence": round(float(group["confidence"]), 4),
        "bbox": {
            "x1": int(group["left"]),
            "y1": int(group["top"]),
            "x2": int(group["right"]),
            "y2": int(group["bottom"]),
        },
    }


def nearby_candidates(label_group, ocr_data, predicate):
    """
    Return typed OCR rows near a label.

    Distance is normalized by OCR text height and image extent rather than
    using a fixed pixel threshold.
    """
    rows = ocr_rows(ocr_data)
    if not rows:
        return []

    scale = max(
        label_group["bottom"] - label_group["top"],
        median_text_height(rows),
        1.0,
    )
    image_right = max(row["_right"] for row in rows)
    image_bottom = max(row["_bottom"] for row in rows)
    max_radius = max(10.0 * scale, 0.12 * math.hypot(image_right, image_bottom))

    label_cx = (label_group["left"] + label_group["right"]) / 2.0
    label_cy = (label_group["top"] + label_group["bottom"]) / 2.0
    output = []

    for row in rows:
        text = normalize_text(row.get("text"))
        if not text or not predicate(text):
            continue

        if (
            row["_top"] >= label_group["top"]
            and row["_bottom"] <= label_group["bottom"]
        ):
            continue

        center_distance = math.hypot(
            row["_cx"] - label_cx,
            row["_cy"] - label_cy,
        )

        vertical_delta = abs(row["_cy"] - label_cy)
        horizontal_delta = abs(row["_cx"] - label_cx)

        same_line = vertical_delta <= max(1.2 * scale, 0.9 * (label_group["bottom"] - label_group["top"]))
        same_column = horizontal_delta <= max(5.0 * scale, label_group["right"] - label_group["left"])

        if same_line:
            relation_bonus = 35.0
        elif same_column:
            relation_bonus = 25.0
        else:
            relation_bonus = 0.0

        if center_distance > max_radius and relation_bonus == 0.0:
            continue

        score = (
            relation_bonus
            + max(0.0, 30.0 - (center_distance / scale) * 2.0)
            + _conf(row.get("conf", 0)) * 20.0
        )
        output.append((score, row))

    return sorted(output, key=lambda item: item[0], reverse=True)
