"""
Product repository integration service.

This layer connects analysis results with the product repository
without mixing persistence logic into the OCR/compliance pipeline.
"""

from datetime import datetime
from pathlib import Path
from shutil import copy2
from uuid import uuid4

from src.repository.models import (
    ImageRecord,
    ProductRecord,
    ScanRecord,
)
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
        product_name_confidence: float | None = None,
        brand_confidence: float | None = None,
    ) -> ProductRecord:
        product_id = f"PROD-{uuid4().hex[:12].upper()}"

        product = ProductRecord(
            product_id=product_id,
            product_name=product_name,
            brand=brand,
            barcode=barcode,
            manufacturer=manufacturer,
            product_name_confidence=(
                product_name_confidence
            ),
            brand_confidence=(
                brand_confidence
            ),
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
        """
        Persist a complete analysis result as a scan.

        The original image is copied into permanent product storage.
        A JSON-safe snapshot of the complete analysis result is stored
        with the scan so History can reconstruct the original result
        without running OCR again.
        """

        product = self.repository.get_product(product_id)

        if product is None:
            raise ValueError(
                f"Product does not exist: {product_id}"
            )

        source_image = Path(image_path)

        if not source_image.exists():
            raise FileNotFoundError(
                f"Scan image does not exist: {source_image}"
            )

        scan_id = f"SCAN-{uuid4().hex[:12].upper()}"

        product_image_dir = (
            self.image_storage_dir / product_id
        )
        product_image_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination_image = (
            product_image_dir
            / f"{scan_id}{source_image.suffix.lower()}"
        )

        copy2(
            source_image,
            destination_image,
        )

        # Force the complete analysis result through JSON
        # serialization so the persisted snapshot contains only
        # JSON-compatible data.
        import json

        analysis_snapshot = json.loads(
            json.dumps(
                analysis_result,
                ensure_ascii=False,
                default=str,
            )
        )

        scan = ScanRecord(
            scan_id=scan_id,
            product_id=product_id,
            image_path=str(destination_image),
            timestamp=datetime.now().isoformat(),
            image_quality=(
                image_quality
                or analysis_snapshot.get("meta", {}).get(
                    "image_quality"
                )
            ),
            ocr=(
                ocr
                or analysis_snapshot.get("meta", {}).get("ocr")
            ),
            compliance=analysis_snapshot.get(
                "legal_metrology_compliance"
            ),
            analysis=analysis_snapshot,
        )

        try:
            saved_scan = self.repository.add_scan(scan)

            # Verify that the complete analysis was actually attached
            # to the scan before returning.
            if saved_scan.analysis is None:
                destination_image.unlink(
                    missing_ok=True
                )
                raise RuntimeError(
                    "Scan was saved without analysis_result."
                )

            return saved_scan

        except Exception:
            destination_image.unlink(
                missing_ok=True
            )
            raise

    def add_product_scan(
        self,
        product_id: str,
        image_paths: list[str | Path],
        analysis_result: dict,
    ) -> ScanRecord:
        """
        Persist one product-level scan containing multiple images.
        """

        product = self.repository.get_product(product_id)

        if product is None:
            raise ValueError(
                f"Product does not exist: {product_id}"
            )

        if not image_paths:
            raise ValueError(
                "At least one image is required."
            )

        scan_id = f"SCAN-{uuid4().hex[:12].upper()}"

        product_image_dir = (
            self.image_storage_dir / product_id
        )

        product_image_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        stored_images = []

        try:
            for image_path in image_paths:
                source_image = Path(image_path)

                if not source_image.exists():
                    raise FileNotFoundError(
                        f"Scan image does not exist: "
                        f"{source_image}"
                    )

                image_id = (
                    f"IMG-{uuid4().hex[:12].upper()}"
                )

                destination = (
                    product_image_dir
                    / (
                        f"{scan_id}_"
                        f"{image_id}"
                        f"{source_image.suffix.lower()}"
                    )
                )

                copy2(
                    source_image,
                    destination,
                )

                stored_images.append(
                    ImageRecord(
                        image_id=image_id,
                        scan_id=scan_id,
                        product_id=product_id,
                        filename=source_image.name,
                        image_path=str(destination),
                        timestamp=datetime.now().isoformat(),
                    )
                )

            import json

            snapshot = json.loads(
                json.dumps(
                    analysis_result,
                    ensure_ascii=False,
                    default=str,
                )
            )

            image_analyses = snapshot.get(
                "images",
                [],
            )

            for image_record, image_entry in zip(
                stored_images,
                image_analyses,
            ):
                # Replace the transient analysis ID with the persisted
                # image ID so API evidence URLs and provenance stay aligned.
                image_entry["image_id"] = image_record.image_id
                image_entry["filename"] = image_record.filename
                image_record.analysis = (
                    image_entry.get("analysis")
                )

                image_record.image_quality = (
                    image_record.analysis.get(
                        "image_quality"
                    )
                    if isinstance(
                        image_record.analysis,
                        dict,
                    )
                    else None
                )

                image_record.ocr = (
                    image_record.analysis.get(
                        "ocr"
                    )
                    if isinstance(
                        image_record.analysis,
                        dict,
                    )
                    else None
                )

            first_image_path = (
                stored_images[0].image_path
            )

            scan = ScanRecord(
                scan_id=scan_id,
                product_id=product_id,
                timestamp=datetime.now().isoformat(),
                images=stored_images,
                image_path=first_image_path,
                image_quality=(
                    stored_images[0].image_quality
                ),
                ocr=(
                    stored_images[0].ocr
                ),
                compliance=snapshot.get(
                    "legal_metrology_compliance"
                ),
                analysis=snapshot,
            )

            saved = self.repository.add_scan(scan)

            return saved

        except Exception:
            for image in stored_images:
                Path(
                    image.image_path
                ).unlink(
                    missing_ok=True
                )

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