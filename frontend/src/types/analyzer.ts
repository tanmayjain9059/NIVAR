export type ComplianceStatus = 'FOUND' | 'REVIEW' | 'NOT_FOUND';

export interface ComplianceCheck {
  label: string;
  detected: boolean | null;
  matched_text?: string | null;
  status: ComplianceStatus;
  conditional?: boolean;
  evidence?: unknown;
  note?: string;
}

export interface LegalMetrologyCompliance {
  overall_status: 'PASS' | 'REVIEW' | 'FAIL';
  checks: Record<string, ComplianceCheck>;
  mandatory_declarations_detected: number;
  mandatory_declarations_total: number;
}

export interface AllergenResult {
  contains: string[];
  may_contain: string[];
}

// Nutrition fields are arbitrary strings mapped to string amounts (e.g. "10g")
export type NutritionResult = Record<string, string>;

export interface AnalysisData {
  source_image: string;
  legal_metrology_compliance: LegalMetrologyCompliance;
  brand: string | null;
  product_name: string | null;
  ingredients: string[];
  allergens: AllergenResult | null;
  nutrition: NutritionResult | null;
  quantity: string | null;
  manufacturer: string | null;
  manufacturing_date: string | null;
  expiry_date: string | null;
  meta: Record<string, any>;
}

export interface AnalyzeResponse {
  success: boolean;
  api_version: string;
  data: AnalysisData;
  warnings: string[];
  errors: string[];
}
