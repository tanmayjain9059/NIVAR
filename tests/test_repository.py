from pathlib import Path

from src.repository.models import (
    ImageRecord,
    ProductRecord,
    ScanRecord,
)
from src.repository.store import ProductRepository


def test_product_can_be_created_and_reloaded(tmp_path):
    storage = tmp_path / "products.json"

    repository = ProductRepository(storage)

    product = ProductRecord(
        product_id="PROD-TEST-001",
        product_name="Premium Rice",
        brand="Test Brand",
    )

    repository.create_product(product)

    loaded = repository.get_product(
        "PROD-TEST-001"
    )

    assert loaded is not None
    assert loaded.product_id == "PROD-TEST-001"
    assert loaded.product_name == "Premium Rice"
    assert loaded.brand == "Test Brand"


def test_multi_image_scan_can_be_persisted_and_reloaded(
    tmp_path,
):
    storage = tmp_path / "products.json"

    repository = ProductRepository(storage)

    product = ProductRecord(
        product_id="PROD-TEST-002",
        product_name="Premium Rice",
        brand="Test Brand",
    )

    repository.create_product(product)

    image_one = ImageRecord(
        image_id="IMG-001",
        scan_id="SCAN-001",
        product_id="PROD-TEST-002",
        filename="front.jpg",
        image_path="data/product_images/front.jpg",
        timestamp="2026-01-01T10:00:00",
        image_quality={
            "status": "GOOD",
        },
        ocr={
            "line_count": 20,
        },
        analysis={
            "source": "front",
        },
    )

    image_two = ImageRecord(
        image_id="IMG-002",
        scan_id="SCAN-001",
        product_id="PROD-TEST-002",
        filename="back.jpg",
        image_path="data/product_images/back.jpg",
        timestamp="2026-01-01T10:00:01",
        image_quality={
            "status": "GOOD",
        },
        ocr={
            "line_count": 30,
        },
        analysis={
            "source": "back",
        },
    )

    scan = ScanRecord(
        scan_id="SCAN-001",
        product_id="PROD-TEST-002",
        timestamp="2026-01-01T10:00:00",
        images=[
            image_one,
            image_two,
        ],
        image_path=image_one.image_path,
        analysis={
            "images_analyzed": 2,
            "product_name": "Premium Rice",
        },
        compliance={
            "overall_status": "COMPLIANT",
        },
    )

    repository.add_scan(scan)

    loaded_scans = repository.get_scans(
        "PROD-TEST-002"
    )

    assert len(loaded_scans) == 1

    loaded_scan = loaded_scans[0]

    assert loaded_scan.scan_id == "SCAN-001"
    assert len(loaded_scan.images) == 2

    assert loaded_scan.images[0].image_id == "IMG-001"
    assert loaded_scan.images[0].filename == "front.jpg"

    assert loaded_scan.images[1].image_id == "IMG-002"
    assert loaded_scan.images[1].filename == "back.jpg"

    assert loaded_scan.analysis["images_analyzed"] == 2
    assert (
        loaded_scan.compliance["overall_status"]
        == "COMPLIANT"
    )


def test_product_scan_history_is_preserved(tmp_path):
    storage = tmp_path / "products.json"

    repository = ProductRepository(storage)

    product = ProductRecord(
        product_id="PROD-TEST-003",
    )

    repository.create_product(product)

    scan_one = ScanRecord(
        scan_id="SCAN-001",
        product_id="PROD-TEST-003",
        timestamp="2026-01-01T10:00:00",
        image_path="front.jpg",
    )

    scan_two = ScanRecord(
        scan_id="SCAN-002",
        product_id="PROD-TEST-003",
        timestamp="2026-01-02T10:00:00",
        image_path="front-new.jpg",
    )

    repository.add_scan(scan_one)
    repository.add_scan(scan_two)

    scans = repository.get_scans(
        "PROD-TEST-003"
    )

    assert len(scans) == 2
    assert scans[0].scan_id == "SCAN-001"
    assert scans[1].scan_id == "SCAN-002"
