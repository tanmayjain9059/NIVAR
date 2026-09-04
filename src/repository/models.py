"""
Data models for the product repository.

The repository stores products and their individual analysis scans.
A product can have multiple scans over time, allowing compliance
history to be maintained.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ScanRecord:
    """
    Represents one analysis performed on a product image.

    The complete analysis result is stored so a previous scan can
    be opened again without running OCR a second time.
    """

    scan_id: str
    product_id: str
    image_path: str
    timestamp: str
    image_quality: Optional[dict[str, Any]] = None
    ocr: Optional[dict[str, Any]] = None
    compliance: Optional[dict[str, Any]] = None

    # Complete analysis response for historical result reconstruction.
    # Optional for backward compatibility with scans created before
    # full analysis persistence was introduced.
    analysis: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the scan record into a JSON-compatible dictionary."""
        return {
            "scan_id": self.scan_id,
            "product_id": self.product_id,
            "image_path": self.image_path,
            "timestamp": self.timestamp,
            "image_quality": self.image_quality,
            "ocr": self.ocr,
            "compliance": self.compliance,
            "analysis": self.analysis,
        }


@dataclass
class ProductRecord:
    """
    Represents a packaged commodity in the repository.

    product_id is the internal identity of the product.
    Barcode is optional and must not be treated as compliance evidence.
    """

    product_id: str
    product_name: Optional[str] = None
    brand: Optional[str] = None
    barcode: Optional[str] = None
    manufacturer: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    scans: list[ScanRecord] = field(default_factory=list)

    def add_scan(self, scan: ScanRecord) -> None:
        """Add a new analysis scan to the product history."""
        self.scans.append(scan)
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert the product record into a JSON-compatible dictionary."""
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "brand": self.brand,
            "barcode": self.barcode,
            "manufacturer": self.manufacturer,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "scans": [
                scan.to_dict()
                for scan in self.scans
            ],
        }