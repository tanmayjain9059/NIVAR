"""
Data models for NIVAR product and scan persistence.

The repository supports:

- Products
- Product-level scans
- Multiple images per scan
- Image-level provenance
- Complete analysis snapshots

Backward compatibility is preserved for older single-image
scan records.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ImageRecord:
    """
    Represents one image belonging to a product-level scan.

    Each image keeps its own provenance so the system can later
    identify which image provided a particular piece of evidence.
    """

    image_id: str
    scan_id: str
    product_id: str
    filename: str
    image_path: str
    timestamp: str

    image_quality: Optional[dict[str, Any]] = None
    ocr: Optional[dict[str, Any]] = None
    analysis: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the image record into a JSON-compatible dictionary.
        """

        return {
            "image_id": self.image_id,
            "scan_id": self.scan_id,
            "product_id": self.product_id,
            "filename": self.filename,
            "image_path": self.image_path,
            "timestamp": self.timestamp,
            "image_quality": self.image_quality,
            "ocr": self.ocr,
            "analysis": self.analysis,
        }


@dataclass
class ScanRecord:
    """
    Represents one product-level analysis scan.

    A scan may contain one or many images.

    For backward compatibility, image_path remains available for
    older single-image scans and represents the first/primary image
    when multiple images are present.
    """

    scan_id: str
    product_id: str
    timestamp: str

    # New multi-image representation.
    images: list[ImageRecord] = field(
        default_factory=list
    )

    # Backward-compatible single-image field.
    image_path: Optional[str] = None

    image_quality: Optional[dict[str, Any]] = None
    ocr: Optional[dict[str, Any]] = None
    compliance: Optional[dict[str, Any]] = None

    # Complete product-level analysis snapshot.
    analysis: Optional[dict[str, Any]] = None

    def add_image(
        self,
        image: ImageRecord,
    ) -> None:
        """
        Add an image to this product-level scan.

        The first image also becomes the backward-compatible
        image_path.
        """

        self.images.append(image)

        if self.image_path is None:
            self.image_path = image.image_path

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the scan record into a JSON-compatible dictionary.
        """

        return {
            "scan_id": self.scan_id,
            "product_id": self.product_id,
            "timestamp": self.timestamp,

            # Backward-compatible field.
            "image_path": self.image_path,

            # New multi-image representation.
            "images": [
                image.to_dict()
                for image in self.images
            ],

            "image_quality": self.image_quality,
            "ocr": self.ocr,
            "compliance": self.compliance,
            "analysis": self.analysis,
        }


@dataclass
class ProductRecord:
    """
    Represents a packaged commodity.

    A product can have multiple scans over time.

    Each scan can contain multiple images, allowing NIVAR to
    combine front, back, side, and additional package images
    into one product-level analysis.
    """

    product_id: str

    product_name: Optional[str] = None
    brand: Optional[str] = None
    barcode: Optional[str] = None
    manufacturer: Optional[str] = None

    # Confidence associated with product identity extraction.
    product_name_confidence: Optional[float] = None
    brand_confidence: Optional[float] = None

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    updated_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    scans: list[ScanRecord] = field(
        default_factory=list
    )

    def add_scan(
        self,
        scan: ScanRecord,
    ) -> None:
        """
        Add a new product-level scan to the product history.
        """

        self.scans.append(scan)

        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the product record into a JSON-compatible dictionary.
        """

        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "brand": self.brand,
            "barcode": self.barcode,
            "manufacturer": self.manufacturer,

            "product_name_confidence": (
                self.product_name_confidence
            ),

            "brand_confidence": (
                self.brand_confidence
            ),

            "created_at": self.created_at,
            "updated_at": self.updated_at,

            "scans": [
                scan.to_dict()
                for scan in self.scans
            ],
        }