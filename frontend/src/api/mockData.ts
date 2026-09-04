import type { AnalyzeResponse } from "../types/analyzer";

export const MOCK_ANALYSIS_RESULT: AnalyzeResponse = {
  success: true,
  api_version: "v1",
  data: {
    source_image: "mock_uploaded_image_url_placeholder",
    legal_metrology_compliance: {
      overall_status: "PASS",
      checks: {
        manufacturer_packer_importer: {
          label: "Manufacturer / Packer / Importer",
          detected: true,
          matched_text: "Example Foods Pvt. Ltd., Plot No. 42, Food Park, Bangalore",
          status: "FOUND"
        },
        net_quantity: {
          label: "Net Quantity",
          detected: true,
          matched_text: "200 g",
          status: "FOUND"
        },
        manufacture_date: {
          label: "Manufacture Date",
          detected: true,
          matched_text: "08/2026",
          status: "FOUND"
        },
        mrp: {
          label: "Maximum Retail Price (MRP)",
          detected: true,
          matched_text: "₹120.00 (Incl. of all taxes)",
          status: "FOUND"
        },
        consumer_care: {
          label: "Consumer Care",
          detected: true,
          matched_text: "1800-XXX-XXXX, support@examplefoods.in",
          status: "FOUND"
        },
        country_of_origin: {
          label: "Country of Origin",
          detected: false,
          conditional: true,
          status: "REVIEW"
        },
        generic_name: {
          label: "Generic Name",
          detected: null,
          status: "REVIEW"
        }
      },
      mandatory_declarations_detected: 5,
      mandatory_declarations_total: 5
    },
    brand: "HealthCrunch",
    product_name: "Oats & Honey Granola Bites",
    ingredients: [
      "Rolled Oats (45%)",
      "Honey (15%)",
      "Almonds",
      "Rice Crisp",
      "Sunflower Oil",
      "Dried Cranberries",
      "Salt",
      "Natural Vanilla Flavor"
    ],
    allergens: {
      contains: ["Oats", "Tree Nuts (Almonds)"],
      may_contain: ["Peanuts", "Soy", "Milk"]
    },
    nutrition: {
      "Energy": "412 kcal",
      "Total Fat": "14 g",
      "Saturated Fat": "1.5 g",
      "Trans Fat": "0 g",
      "Cholesterol": "0 mg",
      "Carbohydrates": "62 g",
      "Total Sugars": "18 g",
      "Added Sugars": "12 g",
      "Protein": "9 g",
      "Sodium": "110 mg"
    },
    quantity: "200 g",
    manufacturer: "Example Foods Pvt. Ltd.",
    manufacturing_date: "08/2026",
    expiry_date: "07/2027",
    meta: {
      ocr_engine: "PaddleOCR (Mock)",
      confidence: "0.94",
      processing_time_ms: "1240"
    }
  },
  warnings: [
    "Country of origin conditionally required but not found."
  ],
  errors: []
};
