"""
Legal Metrology compliance analysis package.
"""

from .extractor import extract_declarations
from .validator import validate_declarations

__all__ = [
    "extract_declarations",
    "validate_declarations",
]
