"""
Simple JSON-backed product repository.

This module handles persistence for products and their scan history.
The storage layer is intentionally kept separate from the analysis
and API layers so it can later be replaced with SQLite/PostgreSQL
without changing the analysis logic.
"""

import json
from pathlib import Path
from typing import Optional

from .models import ProductRecord, ScanRecord


class ProductRepository:
    """JSON-backed repository for products and scan history."""

    def __init__(self, storage_path: str | Path = "data/products.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        """Load repository data from disk."""
        if not self.storage_path.exists():
            return {"products": {}}

        try:
            with open(self.storage_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return {"products": {}}

            data.setdefault("products", {})
            return data

        except (json.JSONDecodeError, OSError):
            return {"products": {}}

    def _save(self, data: dict) -> None:
        """Save repository data to disk."""
        with open(self.storage_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    def create_product(self, product: ProductRecord) -> ProductRecord:
        """Create a new product."""
        data = self._load()

        if product.product_id in data["products"]:
            raise ValueError(
                f"Product already exists: {product.product_id}"
            )

        data["products"][product.product_id] = product.to_dict()
        self._save(data)

        return product

    def get_product(
        self,
        product_id: str,
    ) -> Optional[ProductRecord]:
        """Retrieve a product by its internal product ID."""
        data = self._load()
        raw_product = data["products"].get(product_id)

        if raw_product is None:
            return None

        scans = [
            ScanRecord(
                scan_id=scan["scan_id"],
                product_id=scan["product_id"],
                image_path=scan["image_path"],
                timestamp=scan["timestamp"],
                image_quality=scan.get("image_quality"),
                ocr=scan.get("ocr"),
                compliance=scan.get("compliance"),
            )
            for scan in raw_product.get("scans", [])
        ]

        return ProductRecord(
            product_id=raw_product["product_id"],
            product_name=raw_product.get("product_name"),
            brand=raw_product.get("brand"),
            barcode=raw_product.get("barcode"),
            manufacturer=raw_product.get("manufacturer"),
            created_at=raw_product.get("created_at"),
            updated_at=raw_product.get("updated_at"),
            scans=scans,
        )

    def list_products(self) -> list[ProductRecord]:
        """Return all products in the repository."""
        data = self._load()

        products = []

        for product_id in data["products"]:
            product = self.get_product(product_id)

            if product is not None:
                products.append(product)

        return products

    def add_scan(self, scan: ScanRecord) -> ScanRecord:
        """Add a scan to an existing product."""
        data = self._load()

        if scan.product_id not in data["products"]:
            raise ValueError(
                f"Product does not exist: {scan.product_id}"
            )

        product = self.get_product(scan.product_id)

        if product is None:
            raise ValueError(
                f"Unable to load product: {scan.product_id}"
            )

        product.add_scan(scan)

        data["products"][scan.product_id] = product.to_dict()
        self._save(data)

        return scan

    def get_scans(self, product_id: str) -> list[ScanRecord]:
        """Return the complete scan history of a product."""
        product = self.get_product(product_id)

        if product is None:
            raise ValueError(
                f"Product does not exist: {product_id}"
            )

        return product.scans