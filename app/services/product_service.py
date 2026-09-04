"""
Product repository integration service.

This layer connects analysis results with the product repository
without mixing persistence logic into the OCR/compliance pipeline.
"""

from datetime import datetime
from pathlib import Path
from shutil import copy2
from uuid import uuid4

from src.repository.models import ProductRecord, ScanRecord
from src.repository.store import ProductRepository


class ProductService:
    def __init__(
        self,
        repository: ProductRepository | None = None,
        image_storage_dir: str | Path = "data/product_images",
    ):
        self.repository = repository or ProductRepository()
        self.image_storage_dir = Path(image_storage_dir)

    def create_product(
        self,
        product_name: str | None = None,
        brand: str | None = None,
        barcode: str | None = None,
        manufacturer: str | None = None,
    ) -> ProductRecord:
        product_id = f"PROD-{uuid4().hex[:12].upper()}"

        product = ProductRecord(
            product_id=product_id,
            product_name=product_name,
            brand=brand,
            barcode=barcode,
            manufacturer=manufacturer,
        )

        return self.repository.create_product(product)

    def get_product(self, product_id: str) -> ProductRecord | None:
        return self.repository.get_product(product_id)

    def list_products(self) -> list[ProductRecord]:
        return self.repository.list_products()

    def add_analysis_scan(
        self,
        product_id: str,
        image_path: str | Path,
        analysis_result: dict,
        image_quality: dict | None = None,
        ocr: dict | None = None,
    ) -> ScanRecord:
        product = self.repository.get_product(product_id)

        if product is None:
            raise ValueError(f"Product does not exist: {product_id}")

        scan_id = f"SCAN-{uuid4().hex[:12].upper()}"

        source_image = Path(image_path)

        if not source_image.exists():
            raise FileNotFoundError(
                f"Scan image does not exist: {source_image}"
            )

        product_image_dir = self.image_storage_dir / product_id
        product_image_dir.mkdir(parents=True, exist_ok=True)

        destination_image = (
            product_image_dir
            / f"{scan_id}{source_image.suffix.lower()}"
        )

        copy2(source_image, destination_image)

        scan = ScanRecord(
            scan_id=scan_id,
            product_id=product_id,
            image_path=str(destination_image),
            timestamp=datetime.now().isoformat(),
            image_quality=image_quality,
            ocr=ocr,
            compliance=analysis_result.get(
                "legal_metrology_compliance"
            ),
        )

        try:
            return self.repository.add_scan(scan)

        except Exception:
            destination_image.unlink(missing_ok=True)
            raise

    def get_scan_history(
        self,
        product_id: str,
    ) -> list[ScanRecord]:
        return self.repository.get_scans(product_id)

    def get_scan(
        self,
        product_id: str,
        scan_id: str,
    ) -> ScanRecord | None:
        scans = self.repository.get_scans(product_id)

        for scan in scans:
            if scan.scan_id == scan_id:
                return scan

        return None