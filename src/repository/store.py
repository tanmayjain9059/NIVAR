"""
JSON-backed product repository.

This module handles persistence for:

- Products
- Product scan history
- Multiple images per scan
- Image-level analysis provenance

The storage layer is intentionally isolated from the analysis
and API layers so it can later be replaced by SQLite/PostgreSQL
without changing the higher-level application logic.

Backward compatibility:
Older single-image ScanRecord JSON entries that do not contain
an "images" field are still supported.
"""

import json
from pathlib import Path
from typing import Optional

from .models import (
    ImageRecord,
    ProductRecord,
    ScanRecord,
)


class ProductRepository:
    """
    JSON-backed repository for products and scan history.
    """

    def __init__(
        self,
        storage_path: str | Path = "data/products.json",
    ):
        self.storage_path = Path(storage_path)

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ------------------------------------------------------------------
    # LOW-LEVEL STORAGE
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        """
        Load repository data from disk.

        Invalid or missing storage is treated as an empty repository.
        """

        if not self.storage_path.exists():
            return {
                "products": {}
            }

        try:
            with open(
                self.storage_path,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return {
                    "products": {}
                }

            if not isinstance(
                data.get("products"),
                dict,
            ):
                data["products"] = {}

            return data

        except (
            json.JSONDecodeError,
            OSError,
        ):
            return {
                "products": {}
            }

    def _save(
        self,
        data: dict,
    ) -> None:
        """
        Persist repository data to disk.
        """

        with open(
            self.storage_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

    # ------------------------------------------------------------------
    # PRODUCT SERIALIZATION
    # ------------------------------------------------------------------

    def _deserialize_image(
        self,
        raw_image: dict,
    ) -> ImageRecord:
        """
        Convert persisted image JSON into an ImageRecord.
        """

        return ImageRecord(
            image_id=raw_image["image_id"],
            scan_id=raw_image["scan_id"],
            product_id=raw_image["product_id"],
            filename=raw_image.get(
                "filename",
                "",
            ),
            image_path=raw_image.get(
                "image_path",
                "",
            ),
            timestamp=raw_image.get(
                "timestamp",
                "",
            ),
            image_quality=raw_image.get(
                "image_quality"
            ),
            ocr=raw_image.get(
                "ocr"
            ),
            analysis=raw_image.get(
                "analysis"
            ),
        )

    def _deserialize_scan(
        self,
        raw_scan: dict,
    ) -> ScanRecord:
        """
        Convert persisted scan JSON into a ScanRecord.

        Supports both:

        1. New multi-image scans containing "images".
        2. Older single-image scans without "images".
        """

        raw_images = raw_scan.get(
            "images",
            [],
        )

        images: list[ImageRecord] = []

        if isinstance(
            raw_images,
            list,
        ):
            for raw_image in raw_images:

                if not isinstance(
                    raw_image,
                    dict,
                ):
                    continue

                try:
                    images.append(
                        self._deserialize_image(
                            raw_image
                        )
                    )

                except (
                    KeyError,
                    TypeError,
                ):
                    # Ignore malformed image records rather
                    # than preventing the entire product history
                    # from loading.
                    continue

        return ScanRecord(
            scan_id=raw_scan["scan_id"],
            product_id=raw_scan["product_id"],
            timestamp=raw_scan.get(
                "timestamp",
                "",
            ),

            images=images,

            # This field is retained for old single-image scans.
            image_path=raw_scan.get(
                "image_path"
            ),

            image_quality=raw_scan.get(
                "image_quality"
            ),

            ocr=raw_scan.get(
                "ocr"
            ),

            compliance=raw_scan.get(
                "compliance"
            ),

            analysis=raw_scan.get(
                "analysis"
            ),
        )

    def _deserialize_product(
        self,
        raw_product: dict,
    ) -> ProductRecord:
        """
        Convert persisted product JSON into a ProductRecord.
        """

        raw_scans = raw_product.get(
            "scans",
            [],
        )

        scans: list[ScanRecord] = []

        if isinstance(
            raw_scans,
            list,
        ):
            for raw_scan in raw_scans:

                if not isinstance(
                    raw_scan,
                    dict,
                ):
                    continue

                try:
                    scans.append(
                        self._deserialize_scan(
                            raw_scan
                        )
                    )

                except (
                    KeyError,
                    TypeError,
                ):
                    # Preserve the rest of the product history
                    # if one malformed scan is encountered.
                    continue

        return ProductRecord(
            product_id=raw_product["product_id"],

            product_name=raw_product.get(
                "product_name"
            ),

            brand=raw_product.get(
                "brand"
            ),

            barcode=raw_product.get(
                "barcode"
            ),

            manufacturer=raw_product.get(
                "manufacturer"
            ),

            product_name_confidence=raw_product.get(
                "product_name_confidence"
            ),

            brand_confidence=raw_product.get(
                "brand_confidence"
            ),

            created_at=raw_product.get(
                "created_at"
            ),

            updated_at=raw_product.get(
                "updated_at"
            ),

            scans=scans,
        )

    # ------------------------------------------------------------------
    # PRODUCT OPERATIONS
    # ------------------------------------------------------------------

    def create_product(
        self,
        product: ProductRecord,
    ) -> ProductRecord:
        """
        Create a new product.
        """

        data = self._load()

        if product.product_id in data["products"]:
            raise ValueError(
                f"Product already exists: "
                f"{product.product_id}"
            )

        data["products"][
            product.product_id
        ] = product.to_dict()

        self._save(data)

        return product

    def get_product(
        self,
        product_id: str,
    ) -> Optional[ProductRecord]:
        """
        Retrieve a product by its internal product ID.
        """

        data = self._load()

        raw_product = data[
            "products"
        ].get(
            product_id
        )

        if raw_product is None:
            return None

        if not isinstance(
            raw_product,
            dict,
        ):
            return None

        try:
            return self._deserialize_product(
                raw_product
            )

        except (
            KeyError,
            TypeError,
        ):
            return None

    def list_products(
        self,
    ) -> list[ProductRecord]:
        """
        Return all products in the repository.
        """

        data = self._load()

        products: list[ProductRecord] = []

        for product_id in data[
            "products"
        ]:

            product = self.get_product(
                product_id
            )

            if product is not None:
                products.append(product)

        return products

    # ------------------------------------------------------------------
    # SCAN OPERATIONS
    # ------------------------------------------------------------------

    def add_scan(
        self,
        scan: ScanRecord,
    ) -> ScanRecord:
        """
        Add a product-level scan to an existing product.
        """

        data = self._load()

        if scan.product_id not in data[
            "products"
        ]:
            raise ValueError(
                f"Product does not exist: "
                f"{scan.product_id}"
            )

        product = self.get_product(
            scan.product_id
        )

        if product is None:
            raise ValueError(
                f"Unable to load product: "
                f"{scan.product_id}"
            )

        product.add_scan(
            scan
        )

        data[
            "products"
        ][
            scan.product_id
        ] = product.to_dict()

        self._save(
            data
        )

        return scan

    def get_scans(
        self,
        product_id: str,
    ) -> list[ScanRecord]:
        """
        Return the complete scan history of a product.
        """

        product = self.get_product(
            product_id
        )

        if product is None:
            raise ValueError(
                f"Product does not exist: "
                f"{product_id}"
            )

        return product.scans