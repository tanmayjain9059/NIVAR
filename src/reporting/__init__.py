"""
Reporting package.
"""

from .json_report import (
    build_structured_result,
    generate_pdf_report,
    save_json_result,
)

from .visualization import (
    draw_regions,
    save_debug_images,
)

__all__ = [
    "build_structured_result",
    "generate_pdf_report",
    "save_json_result",
    "draw_regions",
    "save_debug_images",
]