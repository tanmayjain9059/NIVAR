export type ComplianceStatus = "FOUND" | "REVIEW" | "NOT_FOUND";
export type OverallStatus = "COMPLIANT" | "REVIEW" | "NON_COMPLIANT" | "PASS" | "FAIL";
export interface ComplianceCheck { label?: string; detected?: boolean | null; matched_text?: string | null; status: ComplianceStatus; conditional?: boolean; evidence?: any; note?: string; source_images?: string[]; conflict?: boolean; }
export interface LegalMetrologyCompliance { overall_status: OverallStatus; checks: Record<string, ComplianceCheck>; mandatory_declarations_detected: number; mandatory_declarations_total: number; mandatory_declarations_review?: number; mandatory_declarations_missing?: number; disclaimer?: string; }
export interface AllergenResult { contains: string[]; may_contain: string[]; }
export type NutritionResult = Record<string, { value: number | string; unit?: string }>;
export interface AnalysisData { product_id?: string; scan_id?: string; product_name?: string | null; product_name_confidence?: number | null; brand?: string | null; ingredients?: string[]; allergens?: AllergenResult | null; nutrition?: NutritionResult | null; image_quality?: any; legal_metrology_compliance: LegalMetrologyCompliance; images?: Array<{image_id?: string; filename?: string; analysis?: any}>; fusion?: any; [key: string]: any; }
export interface AnalyzeResponse { success: boolean; api_version: string; data: AnalysisData; warnings: string[]; errors: string[]; }
