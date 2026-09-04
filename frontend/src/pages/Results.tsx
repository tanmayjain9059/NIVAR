import { motion, useReducedMotion } from "framer-motion";
import type { AnalyzeResponse, ComplianceCheck } from "../types/analyzer";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RotateCcw,
  ScanLine,
  Package,
  ShieldCheck,
  Leaf,
  AlertOctagon,
  FlaskConical,
  Image as ImageIcon,
} from "lucide-react";

interface ResultsProps {
  result: AnalyzeResponse;
  onRestart: () => void;
}

// ──────────────────────────────────────────────────────────────────────────────
// Status helpers
// ──────────────────────────────────────────────────────────────────────────────

function statusIcon(status: string) {
  if (status === "FOUND") {
    return <CheckCircle2 className="w-4 h-4 text-civic-success" />;
  }

  if (status === "REVIEW") {
    return <AlertTriangle className="w-4 h-4 text-amber-500" />;
  }

  return <XCircle className="w-4 h-4 text-red-500" />;
}

function statusBadge(status: string) {
  const base =
    "text-[11px] font-semibold px-2 py-0.5 rounded-full border";

  if (status === "FOUND") {
    return `${base} bg-civic-success/10 text-civic-success border-civic-success/20`;
  }

  if (status === "REVIEW") {
    return `${base} bg-amber-50 text-amber-600 border-amber-200`;
  }

  return `${base} bg-red-50 text-red-600 border-red-200`;
}

function overallBadge(status: string) {
  // Backend MVP status:
  // 5/5 FOUND -> COMPLIANT
  if (status === "COMPLIANT" || status === "PASS") {
    return {
      label: "COMPLIANT",
      bg: "bg-civic-success/10",
      text: "text-civic-success",
      border: "border-civic-success/30",
      icon: <ShieldCheck className="w-7 h-7 text-civic-success" />,
    };
  }

  if (status === "REVIEW") {
    return {
      label: "REVIEW",
      bg: "bg-amber-50",
      text: "text-amber-600",
      border: "border-amber-200",
      icon: <AlertTriangle className="w-7 h-7 text-amber-500" />,
    };
  }

  return {
    label: "ACTION REQUIRED",
    bg: "bg-red-50",
    text: "text-red-600",
    border: "border-red-200",
    icon: <AlertOctagon className="w-7 h-7 text-red-500" />,
  };
}

// ──────────────────────────────────────────────────────────────────────────────
// Safe value rendering
// ──────────────────────────────────────────────────────────────────────────────

function displayValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }

  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => displayValue(item))
      .filter(Boolean)
      .join(", ");
  }

  if (typeof value === "object") {
    const objectValue = value as {
      value?: unknown;
      unit?: unknown;
    };

    if (
      Object.prototype.hasOwnProperty.call(objectValue, "value") ||
      Object.prototype.hasOwnProperty.call(objectValue, "unit")
    ) {
      const numericValue = displayValue(objectValue.value);
      const unit = displayValue(objectValue.unit);

      return [numericValue, unit].filter(Boolean).join(" ");
    }

    try {
      return JSON.stringify(value);
    } catch {
      return "";
    }
  }

  return String(value);
}

// ──────────────────────────────────────────────────────────────────────────────
// Small shared components
// ──────────────────────────────────────────────────────────────────────────────

function SectionCard({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-4 border-b border-zinc-100">
        <span className="text-civic-primary">{icon}</span>
        <h2 className="text-sm font-semibold text-civic-text">{title}</h2>
      </div>

      <div className="px-5 py-4">{children}</div>
    </div>
  );
}

function Field({
  label,
  value,
}: {
  label: string;
  value: unknown;
}) {
  const renderedValue = displayValue(value);

  return (
    <div>
      <p className="text-[10px] text-civic-muted uppercase tracking-wider mb-0.5">
        {label}
      </p>

      <p className="text-sm text-civic-text font-medium">
        {renderedValue ? (
          renderedValue
        ) : (
          <span className="text-civic-muted italic font-normal">
            Not reliably extracted
          </span>
        )}
      </p>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Compliance section
// ──────────────────────────────────────────────────────────────────────────────

function ComplianceSection({
  compliance,
}: {
  compliance: AnalyzeResponse["data"]["legal_metrology_compliance"];
}) {
  const {
    label,
    bg,
    text,
    border,
    icon,
  } = overallBadge(compliance.overall_status);

  const checks = Object.entries(compliance?.checks ?? {}) as [
    string,
    ComplianceCheck
  ][];

  const detected =
    compliance.mandatory_declarations_detected ?? 0;

  const total =
    compliance.mandatory_declarations_total ?? 0;

  return (
    <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
      {/* Summary header */}
      <div
        className={`px-5 py-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b ${border} bg-gradient-to-r from-white to-zinc-50`}
      >
        <div className="flex items-center gap-4">
          <div
            className={`w-14 h-14 rounded-xl ${bg} border ${border} flex items-center justify-center flex-shrink-0`}
          >
            {icon}
          </div>

          <div>
            <p className="text-[11px] text-civic-secondary uppercase tracking-wider font-medium mb-0.5">
              Legal Metrology Compliance
            </p>

            <p className={`text-2xl font-bold ${text}`}>
              {label}
            </p>
          </div>
        </div>

        <div className="text-right">
          <p className="text-3xl font-bold text-civic-text tabular-nums">
            {detected}

            <span className="text-civic-muted font-normal text-xl">
              /{total}
            </span>
          </p>

          <p className="text-xs text-civic-secondary">
            mandatory declarations detected
          </p>
        </div>
      </div>

      {/* Individual checks */}
      <div className="px-5 py-4 divide-y divide-zinc-100">
        {checks.length === 0 ? (
          <p className="text-sm text-civic-muted italic py-3">
            No compliance checks were returned.
          </p>
        ) : (
          checks.map(([key, check]) => (
            <div key={key} className="flex items-start gap-3 py-3">
              <div className="mt-0.5 flex-shrink-0">
                {statusIcon(check.status)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <p className="text-sm font-medium text-civic-text">
                    {check.label}
                  </p>

                  <span className={statusBadge(check.status)}>
                    {check.status}
                  </span>
                </div>

                {check.matched_text && (
                  <p
                    className="text-xs text-civic-secondary mt-1 truncate"
                    title={displayValue(check.matched_text)}
                  >
                    <span className="text-civic-muted">
                      Detected:{" "}
                    </span>
                    {displayValue(check.matched_text)}
                  </p>
                )}

                {check.conditional && (
                  <p className="text-[10px] text-amber-500 mt-1">
                    Conditionally required — may not apply to all
                    products
                  </p>
                )}

                {check.note && (
                  <p className="text-[10px] text-civic-muted mt-1">
                    {check.note}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Ingredients section
// ──────────────────────────────────────────────────────────────────────────────

function IngredientsSection({
  ingredients,
}: {
  ingredients: string[];
}) {
  if (!ingredients || ingredients.length === 0) {
    return (
      <SectionCard
        title="Ingredients"
        icon={<Leaf className="w-4 h-4" />}
      >
        <p className="text-sm text-civic-muted italic">
          Ingredient information could not be reliably extracted.
        </p>
      </SectionCard>
    );
  }

  return (
    <SectionCard
      title="Ingredients"
      icon={<Leaf className="w-4 h-4" />}
    >
      <p className="text-sm text-civic-text leading-relaxed">
        {ingredients
          .map((ingredient) => displayValue(ingredient))
          .filter(Boolean)
          .join(", ")}
      </p>

      <p className="text-[10px] text-civic-muted mt-3 flex items-center gap-1">
        <ScanLine className="w-3 h-3" />
        Extracted directly from the product label
      </p>
    </SectionCard>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Allergens section
// ──────────────────────────────────────────────────────────────────────────────

function AllergensSection({
  allergens,
}: {
  allergens: AnalyzeResponse["data"]["allergens"];
}) {
  if (
    !allergens ||
    ((allergens.contains?.length ?? 0) === 0 &&
      (allergens.may_contain?.length ?? 0) === 0)
  ) {
    return (
      <SectionCard
        title="Allergens"
        icon={<AlertOctagon className="w-4 h-4" />}
      >
        <p className="text-sm text-civic-muted italic">
          Allergen information could not be reliably extracted.
        </p>
      </SectionCard>
    );
  }

  return (
    <SectionCard
      title="Allergens"
      icon={<AlertOctagon className="w-4 h-4" />}
    >
      {allergens.contains?.length > 0 && (
        <div className="mb-4">
          <p className="text-[10px] font-bold text-red-600 uppercase tracking-wider mb-2">
            Contains
          </p>

          <div className="flex flex-wrap gap-2">
            {allergens.contains.map((a, index) => (
              <span
                key={`${a}-${index}`}
                className="text-xs px-3 py-1 bg-red-50 border border-red-200 text-red-700 rounded-full font-medium"
              >
                {displayValue(a)}
              </span>
            ))}
          </div>
        </div>
      )}

      {allergens.may_contain?.length > 0 && (
        <div>
          <p className="text-[10px] font-bold text-amber-600 uppercase tracking-wider mb-2">
            May Contain
          </p>

          <div className="flex flex-wrap gap-2">
            {allergens.may_contain.map((a, index) => (
              <span
                key={`${a}-${index}`}
                className="text-xs px-3 py-1 bg-amber-50 border border-amber-200 text-amber-700 rounded-full font-medium"
              >
                {displayValue(a)}
              </span>
            ))}
          </div>
        </div>
      )}

      <p className="text-[10px] text-civic-muted mt-4 leading-relaxed">
        Allergen information is extracted from the label. Always
        verify with the physical product.
      </p>
    </SectionCard>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Nutrition section
// ──────────────────────────────────────────────────────────────────────────────

function NutritionSection() {
  return (
    <SectionCard
      title="Advanced Nutrition Analysis"
      icon={<FlaskConical className="w-4 h-4" />}
    >
      <div className="py-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full bg-amber-50 text-amber-600 border border-amber-200">
            Coming Soon
          </span>
        </div>

        <h3 className="text-sm font-semibold text-civic-text mb-2">
          Detailed nutrition analysis
        </h3>

        <p className="text-sm text-civic-muted leading-relaxed">
          Automated extraction of calories, macronutrients, and
          detailed nutrition-table values will be available in a
          future version.
        </p>

        <div className="flex flex-wrap gap-2 mt-4">
          {["Calories", "Macronutrients", "Nutrition Table"].map(
            (item) => (
              <span
                key={item}
                className="text-[11px] px-2.5 py-1 rounded-md bg-zinc-50 border border-zinc-200 text-zinc-500"
              >
                {item}
              </span>
            )
          )}
        </div>
      </div>
    </SectionCard>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Source image
// ──────────────────────────────────────────────────────────────────────────────

function EvidenceSection({
  sourceImage,
}: {
  sourceImage: string;
}) {
  return (
    <SectionCard
      title="Source Image"
      icon={<ImageIcon className="w-4 h-4" />}
    >
      {sourceImage &&
      sourceImage !== "mock_uploaded_image_url_placeholder" ? (
        <div className="rounded-lg overflow-hidden border border-zinc-100">
          <img
            src={sourceImage}
            alt="Original product label"
            className="w-full max-h-72 object-contain bg-zinc-50"
          />
        </div>
      ) : (
        <div className="rounded-lg bg-zinc-50 border border-zinc-200 h-40 flex flex-col items-center justify-center gap-2">
          <ImageIcon className="w-8 h-8 text-zinc-300" />

          <p className="text-xs text-civic-muted">
            Source image not available in this context
          </p>
        </div>
      )}

      <p className="text-[10px] text-civic-muted mt-3">
        OCR bounding-box overlays and region detection will appear
        here when the backend exposes that information.
      </p>
    </SectionCard>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Warnings banner
// ──────────────────────────────────────────────────────────────────────────────

function WarningsBanner({
  warnings,
}: {
  warnings: string[];
}) {
  if (!warnings || warnings.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4">
      <p className="text-xs font-semibold text-amber-700 mb-2 flex items-center gap-1.5">
        <AlertTriangle className="w-3.5 h-3.5" />
        Notices
      </p>

      <ul className="space-y-1">
        {warnings.map((warning, index) => (
          <li
            key={index}
            className="text-xs text-amber-700"
          >
            {displayValue(warning)}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Main Results page
// ──────────────────────────────────────────────────────────────────────────────

export default function Results({
  result,
  onRestart,
}: ResultsProps) {
  const prefersReduced = useReducedMotion();

  if (!result || !result.data) {
    return (
      <div className="min-h-[calc(100vh-3.5rem)] pt-14 bg-civic-bg">
        <div className="max-w-4xl mx-auto px-4 py-12">
          <div className="bg-white rounded-xl border border-red-200 shadow-sm p-8 text-center">
            <AlertOctagon className="w-10 h-10 text-red-500 mx-auto mb-3" />

            <h1 className="text-lg font-semibold text-civic-text">
              Analysis result unavailable
            </h1>

            <p className="text-sm text-civic-secondary mt-2">
              The backend returned an incomplete analysis response.
            </p>

            <button
              onClick={onRestart}
              className="mt-5 flex items-center gap-2 mx-auto bg-civic-primary text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-sm hover:bg-civic-primary/90 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Scan another product
            </button>
          </div>
        </div>
      </div>
    );
  }

  const data = result.data;
  const warnings = result.warnings ?? [];
  const errors = result.errors ?? [];
const compliance = data.legal_metrology_compliance ?? {
  overall_status: "REVIEW" as const,
  checks: {},
  mandatory_declarations_detected: 0,
  mandatory_declarations_total: 0,
};

const complianceStatus =
  compliance.overall_status as string;

const complianceHighlight =
  complianceStatus === "COMPLIANT" ||
  complianceStatus === "PASS"
    ? "text-civic-success"
    : complianceStatus === "REVIEW"
    ? "text-amber-500"
    : "text-red-500";  const containerVariants = {
    hidden: {},
    show: {
      transition: {
        staggerChildren: prefersReduced ? 0 : 0.07,
      },
    },
  };

  const itemVariants = {
    hidden: {
      opacity: 0,
      y: prefersReduced ? 0 : 16,
    },

    show: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.4,
        ease: [0.25, 0.1, 0.25, 1] as const,
      },
    },
  };
const ingredientCount = Array.isArray(data.ingredients)
  ? data.ingredients.length
  : 0;
  return (
    <div className="min-h-[calc(100vh-3.5rem)] pt-14 bg-civic-bg">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Page header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-[11px] text-civic-muted uppercase tracking-wider mb-0.5">
              NIVAR Analysis
            </p>

            <h1 className="text-2xl font-bold text-civic-text tracking-tight">
              {data.product_name ||
                data.brand ||
                "Analysed Product"}
            </h1>

            {data.manufacturer && (
              <p className="text-sm text-civic-secondary mt-0.5">
                {displayValue(data.manufacturer)}
              </p>
            )}
          </div>

          <button
            onClick={onRestart}
            className="flex items-center gap-1.5 px-4 py-2 rounded-full border border-zinc-200 bg-white text-sm text-civic-secondary hover:text-civic-text hover:border-zinc-300 transition-colors shadow-sm"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Scan another
          </button>
        </div>

        {/* Summary stat cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            {
              label: "Compliance",
              value:
                complianceStatus === "PASS"
                  ? "COMPLIANT"
                  : complianceStatus,
              sub: "",
              highlight: complianceHighlight,
            },
            {
              label: "Declarations",
              value: `${compliance.mandatory_declarations_detected ?? 0}/${compliance.mandatory_declarations_total ?? 0}`,
              sub: "detected",
              highlight: "text-civic-text",
            },
            {
              label: "Product Info",
              value: data.product_name
                ? "Available"
                : "Partial",
              sub: "",
              highlight: data.product_name
                ? "text-civic-success"
                : "text-amber-500",
            },
            {
              label: "Food Analysis",
              value:
                ingredientCount > 0
                  ? "Detected"
                  : "Unavailable",
              sub: `${ingredientCount} ingredients`,
              highlight:
                ingredientCount > 0
                  ? "text-civic-success"
                  : "text-civic-muted",
            },
          ].map((card) => (
            <div
              key={card.label}
              className="bg-white rounded-xl border border-zinc-200 shadow-sm px-4 py-4"
            >
              <p className="text-[10px] text-civic-muted uppercase tracking-wider mb-1">
                {card.label}
              </p>

              <p
                className={`text-lg font-bold ${card.highlight} tabular-nums`}
              >
                {card.value}
              </p>

              {card.sub && (
                <p className="text-[10px] text-civic-muted">
                  {card.sub}
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Warnings */}
        {warnings.length > 0 && (
          <div className="mb-6">
            <WarningsBanner warnings={warnings} />
          </div>
        )}

        {/* Main content */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="space-y-5"
        >
          {/* Compliance */}
          <motion.div variants={itemVariants}>
            <ComplianceSection
              compliance={compliance}
            />
          </motion.div>

          {/* Product info + image */}
          <motion.div
            variants={itemVariants}
            className="grid md:grid-cols-2 gap-5"
          >
            <SectionCard
              title="Product Information"
              icon={<Package className="w-4 h-4" />}
            >
              <div className="grid grid-cols-2 gap-x-4 gap-y-4">
                <Field
                  label="Brand"
                  value={data.brand}
                />

                <Field
                  label="Product Name"
                  value={data.product_name}
                />

                <Field
                  label="Net Quantity"
                  value={data.quantity}
                />

                <Field
                  label="MRP"
                  value={
                    compliance.checks?.mrp?.matched_text ??
                    null
                  }
                />

                <Field
                  label="Manufacture Date"
                  value={data.manufacturing_date}
                />

                <Field
                  label="Expiry Date"
                  value={data.expiry_date}
                />

                <div className="col-span-2">
                  <Field
                    label="Manufacturer"
                    value={data.manufacturer}
                  />
                </div>
              </div>
            </SectionCard>

            <EvidenceSection
              sourceImage={data.source_image ?? ""}
            />
          </motion.div>

          {/* Ingredients */}
          <motion.div variants={itemVariants}>
            <IngredientsSection
              ingredients={
                Array.isArray(data.ingredients)
                  ? data.ingredients
                  : []
              }
            />
          </motion.div>

          {/* Allergens + Nutrition */}
          <motion.div
            variants={itemVariants}
            className="grid md:grid-cols-2 gap-5"
          >
            <AllergensSection
              allergens={data.allergens ?? null}
            />

            <NutritionSection />
          </motion.div>

          {/* Errors */}
          {errors.length > 0 && (
            <motion.div
              variants={itemVariants}
              className="rounded-xl border border-red-200 bg-red-50 px-5 py-4"
            >
              <p className="text-xs font-semibold text-red-700 mb-2 flex items-center gap-1.5">
                <AlertOctagon className="w-3.5 h-3.5" />
                Errors
              </p>

              <ul className="space-y-1">
                {errors.map((error, index) => (
                  <li
                    key={index}
                    className="text-xs text-red-600"
                  >
                    {displayValue(error)}
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          {/* Metadata */}
          {data.meta &&
            Object.keys(data.meta).length > 0 && (
              <motion.div variants={itemVariants}>
                <details className="rounded-xl border border-zinc-200 bg-white shadow-sm">
                  <summary className="px-5 py-3 text-xs text-civic-muted cursor-pointer hover:text-civic-secondary select-none">
                    Analysis metadata
                  </summary>

                  <div className="px-5 pb-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {Object.entries(data.meta).map(
                      ([key, value]) => (
                        <div key={key}>
                          <p className="text-[9px] text-civic-muted uppercase tracking-wider">
                            {key.replace(/_/g, " ")}
                          </p>

                          <p className="text-xs text-civic-text font-medium">
                            {displayValue(value)}
                          </p>
                        </div>
                      )
                    )}
                  </div>
                </details>
              </motion.div>
            )}

          {/* Footer */}
          <motion.div
            variants={itemVariants}
            className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-zinc-200"
          >
            <p className="text-[11px] text-civic-muted text-center sm:text-left">
              Results are based on OCR extraction and should be
              verified against the physical product label.
            </p>

            <button
              onClick={onRestart}
              className="flex items-center gap-2 bg-civic-primary text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-sm hover:bg-civic-primary/90 transition-colors flex-shrink-0"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Scan another product
            </button>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}