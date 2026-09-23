# NIVAR API

## Base URL

Local development:

```text
http://127.0.0.1:8000
```

## GET /health

Returns service health.

### Response

```json
{
  "success": true,
  "api_version": "v1",
  "status": "healthy"
}
```

## POST /api/v1/analyze

## POST /api/v1/products/analyze

These endpoints use the same product-level analysis flow.

### Request

Content type:

```text
multipart/form-data
```

Fields:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `images` | file[] | yes | JPG/JPEG/PNG/WEBP |
| `language` | string | no | Defaults to `en` |

Current limits:

- 1–8 images per request
- 15 MB maximum per image

Supported OCR language codes:

```text
en
hi
mr
te
ta
ka
sa
bho
mai
gom
bgc
```

Unsupported language values fall back to `en`.

### Example

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze \
  -F "images=@front.jpg" \
  -F "images=@back.jpg" \
  -F "language=en"
```

### Response envelope

```json
{
  "success": true,
  "api_version": "v1",
  "data": {},
  "warnings": [],
  "errors": []
}
```

Important `data` fields include:

```text
product_id
scan_id
product_name
product_name_confidence
product_name_evidence
brand
brand_confidence
manufacturer
quantity
manufacturing_date
expiry_date
ingredients
allergens
nutrition
legal_metrology_compliance
images
meta
source_image
ocr_language
```

The nested evidence contract can grow as extraction modules evolve.

## Compliance response

The compliance object contains an overall status and declaration-level checks.

Core declaration keys:

```text
manufacturer_packer_importer
net_quantity
manufacture_date
mrp
consumer_care
```

Typical declaration statuses:

```text
FOUND
REVIEW
NOT_FOUND
```

A check can expose:

- matched text/value
- evidence text
- confidence
- bounding box
- reason/note
- manufacturer entity/address fields where relevant

### Status interpretation

- `FOUND` means supporting evidence was detected.
- `REVIEW` means evidence is insufficient for a confident automated conclusion.
- `NOT_FOUND` means the expected declaration was not detected in the searchable evidence.

These are screening statuses, not legal certification.

## GET /api/v1/products/{product_id}/scans/{scan_id}/images/{image_id}

Returns the persisted source image for an image record.

The frontend uses this endpoint to display original scan evidence.

## Error behavior

Common HTTP errors:

- `400`: invalid file, empty upload, unsupported format, size/count violation, or invalid analysis input
- `404`: requested product/scan/image does not exist
- `500`: unexpected backend analysis failure

## Frontend integration

The Vite development server proxies `/api` and `/health` to the local FastAPI service.

Production builds can be served by FastAPI when `frontend/dist` exists.

## API design rule

Clients should depend on this API boundary rather than importing Python implementation modules directly.
