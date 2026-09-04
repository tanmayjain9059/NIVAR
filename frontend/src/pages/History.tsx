import { useEffect, useMemo, useState } from "react";
import {
  History as HistoryIcon,
  Package,
  ChevronRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Loader2,
  Image as ImageIcon,
  FileText,
  ShieldCheck,
  Search,
  FlaskConical,
  Phone,
  Factory,
  Scale,
  CalendarDays,
  IndianRupee,
  Clock3,
} from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:8000";

type BBox = {
  x1?: number;
  y1?: number;
  x2?: number;
  y2?: number;
};

type Evidence = {
  text?: string | null;
  confidence?: number | null;
  bbox?: BBox | null;
  [key: string]: unknown;
};

interface ComplianceCheck {
  status?: string;
  detected?: boolean | null;
  conditional?: boolean;
  matched_text?: string | null;
  value?: string | null;
  evidence?: Evidence | string | null;
  label?: string | null;
  reason?: string | null;
  note?: string | null;
  confidence?: number | null;
  [key: string]: unknown;
}

interface Compliance {
  overall_status?: string;
  mandatory_declarations_detected?: number;
  mandatory_declarations_total?: number;
  mandatory_declarations_review?: number;
  mandatory_declarations_missing?: number;
  checks?: Record<string, ComplianceCheck>;
  declarations?: Record<string, ComplianceCheck>;
  disclaimer?: string;
  [key: string]: unknown;
}

interface ImageQuality {
  accepted?: boolean;
  score?: number;
  reasons?: string[];
  [key: string]: unknown;
}

interface OCRData {
  engine?: string;
  provider?: string;
  text?: string;
  raw_text?: string;
  count?: number;
  total_boxes?: number;
  [key: string]: unknown;
}

interface Analysis {
  source_image?: string;
  product_name?: string | null;
  brand?: string | null;
  barcode?: string | null;
  manufacturer?: string | null;
  quantity?: string | null;
  manufacturing_date?: string | null;
  expiry_date?: string | null;
  product?: Record<string, unknown> | null;
  product_information?: Record<string, unknown> | null;
  ingredients?: unknown;
  allergens?: unknown;
  nutrition?: unknown;
  legal_metrology_compliance?: Compliance | null;
  compliance?: Compliance | null;
  image_quality?: ImageQuality | null;
  ocr?: OCRData | null;
  meta?: Record<string, unknown> | null;
  [key: string]: unknown;
}

interface Scan {
  scan_id: string;
  product_id: string;
  image_path?: string;
  timestamp: string;
  image_quality?: ImageQuality | null;
  ocr?: OCRData | null;
  compliance?: Compliance | null;
  analysis?: Analysis | null;
}

interface Product {
  product_id: string;
  product_name: string | null;
  brand: string | null;
  barcode: string | null;
  manufacturer: string | null;
  created_at: string;
  updated_at: string;
  scans?: Scan[];
}

const CORE_DECLARATIONS = [
  {
    key: "manufacturer_packer_importer",
    label: "Manufacturer / Packer / Importer",
    icon: Factory,
  },
  {
    key: "net_quantity",
    label: "Net Quantity",
    icon: Scale,
  },
  {
    key: "manufacture_date",
    label: "Manufacture / Packing Date",
    icon: CalendarDays,
  },
  {
    key: "mrp",
    label: "Maximum Retail Price (MRP)",
    icon: IndianRupee,
  },
  {
    key: "consumer_care",
    label: "Consumer Care Details",
    icon: Phone,
  },
];

function normalizedStatus(status?: string) {
  return String(status || "").toUpperCase();
}

function isSuccess(status?: string) {
  const value = normalizedStatus(status);
  return value === "FOUND" || value === "PASS" || value === "COMPLIANT";
}

function statusIcon(status?: string) {
  if (isSuccess(status)) {
    return <CheckCircle2 className="w-4 h-4 text-civic-success" />;
  }

  if (normalizedStatus(status) === "REVIEW") {
    return <AlertTriangle className="w-4 h-4 text-amber-500" />;
  }

  return <XCircle className="w-4 h-4 text-red-500" />;
}

function statusClasses(status?: string) {
  if (isSuccess(status)) {
    return "bg-green-50 text-green-700 border-green-200";
  }

  if (normalizedStatus(status) === "REVIEW") {
    return "bg-amber-50 text-amber-700 border-amber-200";
  }

  return "bg-red-50 text-red-700 border-red-200";
}

function overallLabel(status?: string) {
  const value = normalizedStatus(status);

  if (value === "COMPLIANT" || value === "PASS") return "COMPLIANT";
  if (value === "REVIEW") return "REVIEW";
  return "NON-COMPLIANT";
}

function formatDate(value?: string) {
  if (!value) return "Unknown date";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "Not available";

  if (typeof value === "string") {
    return value.trim() || "Not available";
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return "Not available";
    return value.map((item) => formatValue(item)).join(", ");
  }

  return "Available";
}

function getScanImageUrl(scan: Scan) {
  return `${API_BASE_URL}/api/v1/products/${encodeURIComponent(
    scan.product_id
  )}/scans/${encodeURIComponent(scan.scan_id)}/image`;
}

function getCompliance(scan: Scan): Compliance | null {
  return (
    scan.analysis?.legal_metrology_compliance ||
    scan.analysis?.compliance ||
    scan.compliance ||
    null
  );
}

function getChecks(compliance: Compliance | null) {
  if (!compliance) return {};

  if (compliance.checks && typeof compliance.checks === "object") {
    return compliance.checks;
  }

  if (
    compliance.declarations &&
    typeof compliance.declarations === "object"
  ) {
    return compliance.declarations;
  }

  return {};
}

function getEvidenceText(check?: ComplianceCheck) {
  if (!check) return null;

  if (typeof check.evidence === "string") {
    return check.evidence.trim() || null;
  }

  if (
    check.evidence &&
    typeof check.evidence === "object" &&
    typeof check.evidence.text === "string"
  ) {
    return check.evidence.text.trim() || null;
  }

  return null;
}

function getConfidence(check?: ComplianceCheck) {
  if (!check) return null;

  if (
    check.evidence &&
    typeof check.evidence === "object" &&
    typeof check.evidence.confidence === "number"
  ) {
    return check.evidence.confidence;
  }

  return typeof check.confidence === "number" ? check.confidence : null;
}

function getBBox(check?: ComplianceCheck) {
  if (
    check?.evidence &&
    typeof check.evidence === "object" &&
    check.evidence.bbox
  ) {
    return check.evidence.bbox;
  }

  return null;
}

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: unknown;
}) {
  return (
    <div className="py-3 border-b border-zinc-100 last:border-b-0">
      <p className="text-[10px] uppercase tracking-wider text-civic-muted">
        {label}
      </p>
      <p className="text-sm text-civic-text mt-1 whitespace-pre-wrap break-words">
        {formatValue(value)}
      </p>
    </div>
  );
}

function ComplianceCard({
  declaration,
  check,
}: {
  declaration: (typeof CORE_DECLARATIONS)[number];
  check?: ComplianceCheck;
}) {
  const status = check?.status || "NOT_FOUND";
  const evidenceText = getEvidenceText(check);
  const confidence = getConfidence(check);
  const bbox = getBBox(check);
  const Icon = declaration.icon;

  const detectedValue =
    check?.matched_text ??
    check?.value ??
    null;

  return (
    <div className="bg-white rounded-xl border border-zinc-200 p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className="mt-0.5 p-2 rounded-lg bg-zinc-50 border border-zinc-100">
            <Icon className="w-4 h-4 text-civic-secondary" />
          </div>

          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-civic-text">
              {declaration.label}
            </h3>

            <div className="flex items-center gap-2 mt-2">
              {statusIcon(status)}
              <span
                className={`inline-flex items-center px-2 py-1 rounded-full border text-[10px] font-semibold ${statusClasses(
                  status
                )}`}
              >
                {normalizedStatus(status) || "NOT_FOUND"}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-zinc-100 space-y-3">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-civic-muted">
            Detected value
          </p>
          <p className="text-sm text-civic-text mt-1 whitespace-pre-wrap break-words">
            {formatValue(detectedValue)}
          </p>
        </div>

        {evidenceText && evidenceText !== detectedValue && (
          <div>
            <p className="text-[10px] uppercase tracking-wider text-civic-muted">
              OCR evidence
            </p>
            <p className="text-sm text-civic-text mt-1 whitespace-pre-wrap break-words">
              {evidenceText}
            </p>
          </div>
        )}

        {check?.note && (
          <p className="text-xs text-civic-muted leading-relaxed">
            {check.note}
          </p>
        )}

        {check?.reason && (
          <p className="text-xs text-civic-muted leading-relaxed">
            {check.reason}
          </p>
        )}

        <div className="flex flex-wrap gap-3 text-[11px] text-civic-muted">
          {typeof confidence === "number" && (
            <span>
              Confidence:{" "}
              <span className="font-semibold text-civic-text">
                {(confidence * 100).toFixed(1)}%
              </span>
            </span>
          )}

          {bbox &&
            ["x1", "y1", "x2", "y2"].every(
              (key) => typeof bbox[key as keyof BBox] === "number"
            ) && (
              <span>
                Evidence box:{" "}
                <span className="font-medium text-civic-text">
                  ({bbox.x1}, {bbox.y1}) → ({bbox.x2}, {bbox.y2})
                </span>
              </span>
            )}
        </div>
      </div>
    </div>
  );
}

function SectionCard({
  title,
  icon,
  children,
}: {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-zinc-100 flex items-center gap-2">
        {icon && <span className="text-civic-secondary">{icon}</span>}
        <h2 className="text-sm font-semibold text-civic-text">{title}</h2>
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

function ListValue({
  title,
  values,
}: {
  title: string;
  values: unknown;
}) {
  if (!Array.isArray(values) || values.length === 0) return null;

  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-civic-muted mb-2">
        {title}
      </p>

      <div className="flex flex-wrap gap-2">
        {values.map((value, index) => (
          <span
            key={`${String(value)}-${index}`}
            className="text-xs px-2.5 py-1 rounded-full bg-zinc-50 border border-zinc-200 text-civic-text"
          >
            {formatValue(value)}
          </span>
        ))}
      </div>
    </div>
  );
}

function IngredientsSection({ ingredients }: { ingredients: unknown }) {
  const values = Array.isArray(ingredients) ? ingredients : [];

  return (
    <SectionCard
      title="Ingredients"
      icon={<FileText className="w-4 h-4" />}
    >
      {values.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {values.map((item, index) => (
            <span
              key={`${String(item)}-${index}`}
              className="text-xs px-2.5 py-1.5 rounded-lg bg-zinc-50 border border-zinc-200 text-civic-text"
            >
              {formatValue(item)}
            </span>
          ))}
        </div>
      ) : (
        <p className="text-sm text-civic-muted">
          No ingredient information was stored for this scan.
        </p>
      )}
    </SectionCard>
  );
}

function AllergensSection({ allergens }: { allergens: unknown }) {
  if (!allergens || typeof allergens !== "object") {
    return (
      <SectionCard
        title="Allergen Analysis"
        icon={<ShieldCheck className="w-4 h-4" />}
      >
        <p className="text-sm text-civic-muted">
          No allergen information was stored for this scan.
        </p>
      </SectionCard>
    );
  }

  const data = allergens as Record<string, unknown>;
  const contains = data.contains;
  const mayContain = data.may_contain;

  return (
    <SectionCard
      title="Allergen Analysis"
      icon={<ShieldCheck className="w-4 h-4" />}
    >
      <div className="space-y-4">
        <ListValue title="Contains" values={contains} />
        <ListValue title="May contain" values={mayContain} />

        {!Array.isArray(contains) &&
          !Array.isArray(mayContain) && (
            <p className="text-sm text-civic-muted">
              {formatValue(allergens)}
            </p>
          )}
      </div>
    </SectionCard>
  );
}

function NutritionSection() {
  return (
    <SectionCard
      title="Advanced Nutrition Analysis"
      icon={<FlaskConical className="w-4 h-4" />}
    >
      <div className="py-2">
        <span className="inline-flex items-center px-2 py-1 rounded-full bg-amber-50 text-amber-600 border border-amber-200 text-[10px] font-bold uppercase tracking-wider">
          Coming Soon
        </span>

        <h3 className="text-sm font-semibold text-civic-text mt-3">
          Detailed nutrition analysis
        </h3>

        <p className="text-sm text-civic-muted leading-relaxed mt-2">
          Automated extraction of calories, macronutrients, and detailed
          nutrition-table values will be available in a future version.
        </p>

        <div className="flex flex-wrap gap-2 mt-4">
          {["Calories", "Macronutrients", "Nutrition Table"].map((item) => (
            <span
              key={item}
              className="text-[11px] px-2.5 py-1 rounded-md bg-zinc-50 border border-zinc-200 text-zinc-500"
            >
              {item}
            </span>
          ))}
        </div>
      </div>
    </SectionCard>
  );
}

function QualityCard({ quality }: { quality: ImageQuality | null }) {
  if (!quality) return null;

  return (
    <SectionCard
      title="Image Quality"
      icon={<ImageIcon className="w-4 h-4" />}
    >
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-civic-muted">
            Status
          </p>
          <p className="text-sm font-semibold text-civic-text mt-1">
            {quality.accepted === false ? "Rejected" : "Accepted"}
          </p>
        </div>

        <div>
          <p className="text-[10px] uppercase tracking-wider text-civic-muted">
            Quality Score
          </p>
          <p className="text-sm font-semibold text-civic-text mt-1">
            {typeof quality.score === "number"
              ? `${quality.score.toFixed(1)} / 100`
              : "Not available"}
          </p>
        </div>

        <div className="col-span-2 sm:col-span-1">
          <p className="text-[10px] uppercase tracking-wider text-civic-muted">
            Quality Notes
          </p>
          <p className="text-sm text-civic-text mt-1">
            {quality.reasons?.length
              ? quality.reasons.join(" • ")
              : "No issues reported"}
          </p>
        </div>
      </div>
    </SectionCard>
  );
}

function OCRSummary({ ocr }: { ocr: OCRData | null }) {
  if (!ocr) return null;

  const rawText = ocr.raw_text || ocr.text;

  return (
    <SectionCard title="OCR Summary" icon={<Search className="w-4 h-4" />}>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-4">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-civic-muted">
            Engine
          </p>
          <p className="text-sm font-medium text-civic-text mt-1">
            {formatValue(ocr.engine || ocr.provider)}
          </p>
        </div>

        <div>
          <p className="text-[10px] uppercase tracking-wider text-civic-muted">
            Detected boxes
          </p>
          <p className="text-sm font-medium text-civic-text mt-1">
            {formatValue(ocr.count ?? ocr.total_boxes)}
          </p>
        </div>
      </div>

      {rawText && (
        <details className="border border-zinc-200 rounded-lg">
          <summary className="px-3 py-2 text-xs font-medium text-civic-text cursor-pointer select-none">
            View extracted text
          </summary>
          <pre className="px-3 py-3 text-[11px] text-civic-muted whitespace-pre-wrap break-words border-t border-zinc-100 max-h-72 overflow-auto">
            {rawText}
          </pre>
        </details>
      )}
    </SectionCard>
  );
}

export default function History() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [selectedScan, setSelectedScan] = useState<Scan | null>(null);

  const [loading, setLoading] = useState(true);
  const [scansLoading, setScansLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sortedProducts = useMemo(() => {
    return products
      .filter((product) => (product.scans?.length ?? 0) > 0)
      .slice()
      .sort(
        (a, b) =>
          new Date(b.updated_at).getTime() -
          new Date(a.updated_at).getTime()
      );
  }, [products]);

  useEffect(() => {
    async function loadProducts() {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`${API_BASE_URL}/api/v1/products`);

        if (!response.ok) {
          throw new Error("Failed to load scan history.");
        }

        const data = await response.json();

        setProducts(Array.isArray(data?.data) ? data.data : []);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load scan history."
        );
      } finally {
        setLoading(false);
      }
    }

    loadProducts();
  }, []);

  async function openProduct(product: Product) {
    try {
      setSelectedProduct(product);
      setSelectedScan(null);
      setScans([]);
      setScansLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/products/${encodeURIComponent(
          product.product_id
        )}/scans`
      );

      if (!response.ok) {
        throw new Error("Failed to load scan history.");
      }

      const data = await response.json();

      const loadedScans: Scan[] = Array.isArray(data?.data) ? data.data : [];

      setScans(
        loadedScans.slice().sort(
          (a, b) =>
            new Date(b.timestamp).getTime() -
            new Date(a.timestamp).getTime()
        )
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load scan history."
      );
    } finally {
      setScansLoading(false);
    }
  }

  async function openScan(scan: Scan) {
    try {
      setDetailLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/products/${encodeURIComponent(
          scan.product_id
        )}/scans/${encodeURIComponent(scan.scan_id)}`
      );

      if (!response.ok) {
        throw new Error("Failed to load scan details.");
      }

      const data = await response.json();

      if (!data?.data) {
        throw new Error("Scan details are not available.");
      }

      setSelectedScan(data.data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load scan details."
      );
    } finally {
      setDetailLoading(false);
    }
  }

  async function downloadReport(scan: Scan) {
    try {
      setReportLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/products/${encodeURIComponent(
          scan.product_id
        )}/scans/${encodeURIComponent(scan.scan_id)}/report`
      );

      if (!response.ok) {
        let message = "Failed to generate PDF report.";

        try {
          const data = await response.json();

          if (typeof data?.detail === "string" && data.detail.trim()) {
            message = data.detail;
          }
        } catch {
          // Keep the default message when the server does not return JSON.
        }

        throw new Error(message);
      }

      const blob = await response.blob();

      if (blob.size === 0) {
        throw new Error("The generated PDF report is empty.");
      }

      const contentType = response.headers.get("content-type") || "";

      if (!contentType.includes("application/pdf")) {
        throw new Error(
          "The server did not return a PDF report."
        );
      }

      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");

      anchor.href = url;
      anchor.download = `compliance_report_${scan.scan_id}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate PDF report."
      );
    } finally {
      setReportLoading(false);
    }
  }

  function goBackToHistory() {
    setSelectedProduct(null);
    setSelectedScan(null);
    setScans([]);
    setError(null);
  }

  function goBackToScans() {
    setSelectedScan(null);
    setError(null);
  }

  if (selectedProduct && selectedScan) {
    const compliance = getCompliance(selectedScan);
    const checks = getChecks(compliance);
    const overallStatus = compliance?.overall_status || "REVIEW";
    const quality =
      selectedScan.image_quality ||
      selectedScan.analysis?.image_quality ||
      null;
    const ocr = selectedScan.ocr || selectedScan.analysis?.ocr || null;
    const analysis = selectedScan.analysis;

    const productInfo =
      analysis?.product_information ||
      analysis?.product ||
      null;

    const productName =
      analysis?.product_name ||
      selectedProduct.product_name ||
      "Unnamed Product";

    const manufacturer =
      analysis?.manufacturer ||
      selectedProduct.manufacturer ||
      null;

    const ingredientData =
      analysis?.ingredients ?? null;

    const allergenData =
      analysis?.allergens ?? null;

    return (
      <div className="flex-1 pt-14 bg-civic-bg min-h-screen">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-8">
          <button
            onClick={goBackToScans}
            className="inline-flex items-center gap-2 text-sm text-civic-muted hover:text-civic-text transition-colors mb-5"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to scans
          </button>

          {error && (
            <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5 mb-7">
            <div>
              <div className="flex items-center gap-2 text-xs text-civic-muted mb-2">
                <HistoryIcon className="w-4 h-4" />
                Scan history
                <ChevronRight className="w-3 h-3" />
                {productName}
              </div>

              <h1 className="text-2xl sm:text-3xl font-bold text-civic-text">
                Scan Details
              </h1>

              <p className="text-sm text-civic-muted mt-1">
                {formatDate(selectedScan.timestamp)}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3 self-start">
              <button
                type="button"
                onClick={() => downloadReport(selectedScan)}
                disabled={reportLoading}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-zinc-200 bg-white text-civic-text text-xs font-semibold shadow-sm hover:border-zinc-300 hover:bg-zinc-50 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {reportLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <FileText className="w-4 h-4" />
                )}
                {reportLoading ? "Generating PDF…" : "Generate PDF Report"}
              </button>

              <div
                className={`inline-flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-bold ${statusClasses(
                  overallStatus
                )}`}
              >
                {statusIcon(overallStatus)}
                {overallLabel(overallStatus)}
              </div>
            </div>
          </div>

          <div className="grid lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.9fr)] gap-5 mb-5">
            <SectionCard
              title="Scanned Product"
              icon={<ImageIcon className="w-4 h-4" />}
            >
              <div className="rounded-xl overflow-hidden border border-zinc-200 bg-zinc-50">
                <img
                  src={getScanImageUrl(selectedScan)}
                  alt={`${productName} scanned label`}
                  className="w-full max-h-[560px] object-contain"
                  onError={(event) => {
                    event.currentTarget.style.display = "none";
                    event.currentTarget.parentElement?.classList.add(
                      "min-h-[280px]"
                    );
                  }}
                />
              </div>
            </SectionCard>

            <SectionCard
              title="Product Information"
              icon={<Package className="w-4 h-4" />}
            >
              <div>
                <DetailRow label="Product Name" value={productName} />
                <DetailRow
                  label="Brand"
                  value={
                    analysis?.brand ||
                    selectedProduct.brand ||
                    productInfo?.brand ||
                    null
                  }
                />
                <DetailRow
                  label="Manufacturer"
                  value={manufacturer || productInfo?.manufacturer}
                />
                <DetailRow
                  label="Barcode"
                  value={
                    analysis?.barcode ||
                    selectedProduct.barcode ||
                    productInfo?.barcode
                  }
                />
                <DetailRow
                  label="Net Quantity"
                  value={analysis?.quantity || productInfo?.quantity}
                />
                <DetailRow
                  label="Manufacture Date"
                  value={analysis?.manufacturing_date}
                />
                <DetailRow
                  label="Expiry Date"
                  value={analysis?.expiry_date}
                />
              </div>
            </SectionCard>
          </div>

          <div className="mb-5">
            <SectionCard
              title="Legal Metrology Compliance"
              icon={<ShieldCheck className="w-4 h-4" />}
            >
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-5">
                <div className="rounded-lg bg-zinc-50 border border-zinc-200 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-civic-muted">
                    Overall
                  </p>
                  <p className="text-sm font-bold text-civic-text mt-1">
                    {overallLabel(overallStatus)}
                  </p>
                </div>

                <div className="rounded-lg bg-zinc-50 border border-zinc-200 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-civic-muted">
                    Detected
                  </p>
                  <p className="text-sm font-bold text-civic-text mt-1">
                    {compliance?.mandatory_declarations_detected ?? "—"} /{" "}
                    {compliance?.mandatory_declarations_total ?? 5}
                  </p>
                </div>

                <div className="rounded-lg bg-zinc-50 border border-zinc-200 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-civic-muted">
                    Review
                  </p>
                  <p className="text-sm font-bold text-civic-text mt-1">
                    {compliance?.mandatory_declarations_review ?? 0}
                  </p>
                </div>

                <div className="rounded-lg bg-zinc-50 border border-zinc-200 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-civic-muted">
                    Missing
                  </p>
                  <p className="text-sm font-bold text-civic-text mt-1">
                    {compliance?.mandatory_declarations_missing ?? 0}
                  </p>
                </div>

                <div className="rounded-lg bg-zinc-50 border border-zinc-200 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-civic-muted">
                    Core Checks
                  </p>
                  <p className="text-sm font-bold text-civic-text mt-1">
                    5
                  </p>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                {CORE_DECLARATIONS.map((declaration) => (
                  <ComplianceCard
                    key={declaration.key}
                    declaration={declaration}
                    check={checks[declaration.key]}
                  />
                ))}
              </div>

              {compliance?.disclaimer && (
                <p className="text-[11px] text-civic-muted leading-relaxed mt-5 pt-4 border-t border-zinc-100">
                  {compliance.disclaimer}
                </p>
              )}
            </SectionCard>
          </div>

          <div className="grid lg:grid-cols-2 gap-5 mb-5">
            <IngredientsSection ingredients={ingredientData} />
            <AllergensSection allergens={allergenData} />
          </div>

          <div className="mb-5">
            <NutritionSection />
          </div>

          <div className="grid lg:grid-cols-2 gap-5 mb-5">
            <QualityCard quality={quality} />
            <OCRSummary ocr={ocr} />
          </div>

          <SectionCard
            title="Scan Metadata"
            icon={<Clock3 className="w-4 h-4" />}
          >
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-civic-muted">
                  Scan ID
                </p>
                <p className="text-xs font-mono text-civic-text mt-1 break-all">
                  {selectedScan.scan_id}
                </p>
              </div>

              <div>
                <p className="text-[10px] uppercase tracking-wider text-civic-muted">
                  Product ID
                </p>
                <p className="text-xs font-mono text-civic-text mt-1 break-all">
                  {selectedScan.product_id}
                </p>
              </div>

              <div>
                <p className="text-[10px] uppercase tracking-wider text-civic-muted">
                  Scan Time
                </p>
                <p className="text-xs text-civic-text mt-1">
                  {formatDate(selectedScan.timestamp)}
                </p>
              </div>

              <div>
                <p className="text-[10px] uppercase tracking-wider text-civic-muted">
                  Stored Image
                </p>
                <p className="text-xs text-civic-text mt-1">
                  Available
                </p>
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    );
  }

  if (selectedProduct) {
    return (
      <div className="flex-1 pt-14 bg-civic-bg min-h-screen">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-8">
          <button
            onClick={goBackToHistory}
            className="inline-flex items-center gap-2 text-sm text-civic-muted hover:text-civic-text transition-colors mb-5"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to history
          </button>

          <div className="mb-7">
            <p className="text-xs text-civic-muted mb-1">Product history</p>
            <h1 className="text-2xl sm:text-3xl font-bold text-civic-text">
              {selectedProduct.product_name || "Unnamed Product"}
            </h1>
            <p className="text-sm text-civic-muted mt-1">
              {scans.length} {scans.length === 1 ? "scan" : "scans"}
            </p>
          </div>

          {error && (
            <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {scansLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-6 h-6 animate-spin text-civic-secondary" />
            </div>
          ) : scans.length === 0 ? (
            <div className="rounded-xl border border-zinc-200 bg-white p-10 text-center">
              <FileText className="w-8 h-8 text-zinc-300 mx-auto mb-3" />
              <p className="text-sm text-civic-muted">
                No scans found for this product.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {scans.map((scan) => {
                const compliance = getCompliance(scan);
                const status = compliance?.overall_status || "REVIEW";

                return (
                  <button
                    key={scan.scan_id}
                    onClick={() => openScan(scan)}
                    disabled={detailLoading}
                    className="w-full text-left bg-white rounded-xl border border-zinc-200 p-4 hover:border-zinc-300 hover:shadow-sm transition-all disabled:opacity-60"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 rounded-lg overflow-hidden bg-zinc-50 border border-zinc-200 flex-shrink-0">
                        <img
                          src={getScanImageUrl(scan)}
                          alt=""
                          className="w-full h-full object-cover"
                        />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full border text-[10px] font-semibold ${statusClasses(
                              status
                            )}`}
                          >
                            {statusIcon(status)}
                            {overallLabel(status)}
                          </span>
                        </div>

                        <p className="text-sm font-medium text-civic-text mt-2">
                          {formatDate(scan.timestamp)}
                        </p>

                        <p className="text-[11px] text-civic-muted font-mono mt-1 truncate">
                          {scan.scan_id}
                        </p>
                      </div>

                      <ChevronRight className="w-5 h-5 text-zinc-300 flex-shrink-0" />
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 pt-14 bg-civic-bg min-h-screen">
      <div className="max-w-5xl mx-auto px-5 sm:px-8 py-8">
        <div className="mb-7">
          <div className="flex items-center gap-2 text-xs text-civic-muted mb-2">
            <HistoryIcon className="w-4 h-4" />
            Scan History
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-civic-text">
            Previous Scans
          </h1>

          <p className="text-sm text-civic-muted mt-1">
            Review complete results from previously processed products.
          </p>
        </div>

        {error && (
          <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin text-civic-secondary" />
          </div>
        ) : sortedProducts.length === 0 ? (
          <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center">
            <Package className="w-10 h-10 text-zinc-300 mx-auto mb-4" />
            <h2 className="text-sm font-semibold text-civic-text">
              No scan history yet
            </h2>
            <p className="text-sm text-civic-muted mt-1">
              Completed product scans will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {sortedProducts.map((product) => {
              const productScans = product.scans || [];
              const latestScan = productScans
                .slice()
                .sort(
                  (a, b) =>
                    new Date(b.timestamp).getTime() -
                    new Date(a.timestamp).getTime()
                )[0];

              const compliance = latestScan
                ? getCompliance(latestScan)
                : null;

              const status = compliance?.overall_status || "REVIEW";

              return (
                <button
                  key={product.product_id}
                  onClick={() => openProduct(product)}
                  className="w-full text-left bg-white rounded-xl border border-zinc-200 p-4 hover:border-zinc-300 hover:shadow-sm transition-all"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-zinc-50 border border-zinc-200 flex items-center justify-center flex-shrink-0">
                      <Package className="w-6 h-6 text-civic-secondary" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="text-sm font-semibold text-civic-text truncate">
                          {product.product_name || "Unnamed Product"}
                        </h2>

                        <span
                          className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full border text-[10px] font-semibold ${statusClasses(
                            status
                          )}`}
                        >
                          {statusIcon(status)}
                          {overallLabel(status)}
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-[11px] text-civic-muted">
                        <span>
                          {productScans.length}{" "}
                          {productScans.length === 1 ? "scan" : "scans"}
                        </span>

                        <span>
                          Latest: {formatDate(latestScan?.timestamp)}
                        </span>
                      </div>
                    </div>

                    <ChevronRight className="w-5 h-5 text-zinc-300 flex-shrink-0" />
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {detailLoading && (
        <div className="fixed inset-0 z-50 bg-black/10 flex items-center justify-center pointer-events-none">
          <div className="bg-white rounded-xl border border-zinc-200 shadow-lg px-4 py-3 flex items-center gap-2 text-sm text-civic-text">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading scan details…
          </div>
        </div>
      )}
    </div>
  );
}
