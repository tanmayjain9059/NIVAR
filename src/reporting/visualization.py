"""
Debug image generation and region visualization.
"""

from pathlib import Path

import cv2


REGION_COLORS = {
    "ingredients": (0, 255, 0),
    "nutrition": (255, 0, 0),
    "allergens": (0, 0, 255),
    "compliance": (0, 255, 255),
}


def draw_regions(image, regions):
    """
    Draw detected regions on an image.
    """

    preview = image.copy()

    for name, region in regions.items():

        if region is None:
            continue

        x1 = region["x1"]
        y1 = region["y1"]
        x2 = region["x2"]
        y2 = region["y2"]

        color = REGION_COLORS.get(
            name,
            (255, 255, 255),
        )

        cv2.rectangle(
            preview,
            (x1, y1),
            (x2, y2),
            color,
            8,
        )

        cv2.putText(
            preview,
            name.upper(),
            (x1, max(50, y1 - 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            color,
            4,
        )

    return preview


def save_debug_images(
    processed,
    regions,
    rois,
    source_image_path,
    output_dir="results",
):
    """
    Save region overlay and individual ROI images.
    """

    debug_dir = (
        Path(output_dir)
        / "debug"
    )

    debug_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    stem = Path(
        source_image_path
    ).stem

    preview = draw_regions(
        processed,
        regions,
    )

    cv2.imwrite(
        str(
            debug_dir
            / f"{stem}_regions.jpg"
        ),
        preview,
    )

    for name, roi in rois.items():

        if roi is None:
            continue

        cv2.imwrite(
            str(
                debug_dir
                / f"{stem}_{name}_roi.jpg"
            ),
            roi,
        )

    print(
        f"Debug images saved to: {debug_dir}"
    )
