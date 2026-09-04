import { useRef } from "react";
import {
  motion,
  useScroll,
  useTransform,
  useReducedMotion,
} from "framer-motion";
import {
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  ScanLine,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

interface HomeProps {
  onStart: () => void;
}

// ──────────────────────────────────────────────────────────────────────────────
// Scroll-driven label intelligence story
// ──────────────────────────────────────────────────────────────────────────────
function StorySection({ onStart }: HomeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const prefersReduced = useReducedMotion();

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  const pkgScale = useTransform(scrollYProgress, [0, 0.12], [0.88, 1]);
  const pkgY = useTransform(
    scrollYProgress,
    [0, 0.12, 0.52, 0.78],
    [0, 0, -35, -95]
  );
  const pkgOpacity = useTransform(
    scrollYProgress,
    [0, 0.72, 0.84],
    [1, 1, 0]
  );

  const scanProgress = useTransform(scrollYProgress, [0.08, 0.42], [0, 100]);

  const mrpO = useTransform(scrollYProgress, [0.16, 0.26, 0.66], [0, 1, 0]);
  const mrpX = useTransform(scrollYProgress, [0.16, 0.26], [0, -145]);
  const mrpY = useTransform(scrollYProgress, [0.16, 0.26], [8, -70]);

  const qtyO = useTransform(scrollYProgress, [0.22, 0.32, 0.66], [0, 1, 0]);
  const qtyX = useTransform(scrollYProgress, [0.22, 0.32], [0, -155]);
  const qtyY = useTransform(scrollYProgress, [0.22, 0.32], [8, 45]);

  const mfgO = useTransform(scrollYProgress, [0.28, 0.38, 0.66], [0, 1, 0]);
  const mfgX = useTransform(scrollYProgress, [0.28, 0.38], [0, 155]);
  const mfgY = useTransform(scrollYProgress, [0.28, 0.38], [8, -55]);

  const ingO = useTransform(scrollYProgress, [0.34, 0.44, 0.66], [0, 1, 0]);
  const ingX = useTransform(scrollYProgress, [0.34, 0.44], [0, 150]);
  const ingY = useTransform(scrollYProgress, [0.34, 0.44], [8, 55]);

  const dateO = useTransform(scrollYProgress, [0.40, 0.50, 0.66], [0, 1, 0]);
  const dateX = useTransform(scrollYProgress, [0.40, 0.50], [0, -135]);
  const dateY = useTransform(scrollYProgress, [0.40, 0.50], [8, 75]);

  const dashO = useTransform(scrollYProgress, [0.58, 0.72], [0, 1]);
  const dashY = useTransform(scrollYProgress, [0.58, 0.72], [45, 0]);
  const dashScale = useTransform(scrollYProgress, [0.58, 0.72], [0.97, 1]);

  const ctaO = useTransform(scrollYProgress, [0.76, 0.88], [0, 1]);
  const ctaY = useTransform(scrollYProgress, [0.76, 0.88], [22, 0]);

  return (
    <div ref={containerRef} className="relative h-[360vh]">
      <div className="sticky top-0 h-screen flex items-center justify-center overflow-hidden bg-civic-bg">
        <div className="absolute inset-0 bg-[radial-gradient(#b0b8ba_1px,transparent_1px)] [background-size:24px_24px] opacity-30 pointer-events-none" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[32rem] h-[32rem] rounded-full bg-civic-primary/5 blur-3xl pointer-events-none" />

        {/* Process label */}
        <div className="absolute top-8 left-1/2 -translate-x-1/2 z-40 text-center">
          <div className="inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-civic-secondary">
            <Sparkles className="w-3.5 h-3.5 text-civic-primary" />
            From label to evidence
          </div>
        </div>

        {/* Fictional package */}
        <motion.div
          style={{
            scale: prefersReduced ? 1 : pkgScale,
            y: prefersReduced ? 0 : pkgY,
            opacity: prefersReduced ? 1 : pkgOpacity,
          }}
          className="relative z-10 w-52 h-72 sm:w-60 sm:h-[19rem] bg-white rounded-2xl shadow-2xl border border-zinc-200 flex flex-col overflow-hidden select-none"
        >
          <div className="flex-shrink-0 h-28 bg-gradient-to-br from-civic-primary/10 to-civic-accent flex items-center justify-center relative overflow-hidden">
            <div className="absolute top-2 right-2 text-[8px] text-civic-primary/40 font-mono">
              DEMO LABEL
            </div>
            <span className="text-civic-primary font-extrabold text-2xl tracking-tighter z-10">
              OatBites
            </span>
          </div>

          <div className="flex-1 p-3 flex flex-col gap-1.5">
            <div className="text-[11px] font-semibold text-civic-text">
              Oats & Honey Granola
            </div>
            <div className="text-[10px] text-civic-secondary">
              Net Qty: 200 g
            </div>
            <div className="text-[10px] text-civic-secondary">
              MRP: ₹120.00 (incl. taxes)
            </div>
            <div className="mt-auto pt-2 border-t border-zinc-100 text-[8.5px] text-civic-muted leading-relaxed">
              Mfg: Example Foods Pvt. Ltd., Food Park, Bangalore
              <br />
              Mfg: 08/2026 &nbsp;|&nbsp; Exp: 07/2027
            </div>
          </div>

          <motion.div
            style={{
              top: prefersReduced
                ? "50%"
                : useTransform(scanProgress, (v) => `${v}%`),
            }}
            className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-civic-primary to-transparent opacity-80 shadow-[0_0_8px_rgba(17,94,89,0.55)] z-20 pointer-events-none"
          />
        </motion.div>

        {!prefersReduced && (
          <>
            <DataChip
              label="Maximum Retail Price"
              value="₹ 120.00"
              style={{ opacity: mrpO, x: mrpX, y: mrpY }}
            />
            <DataChip
              label="Net Quantity"
              value="200 g"
              style={{ opacity: qtyO, x: qtyX, y: qtyY }}
            />
            <DataChip
              label="Manufacturer"
              value="Example Foods Pvt. Ltd."
              style={{ opacity: mfgO, x: mfgX, y: mfgY }}
              wide
            />
            <DataChip
              label="Ingredients"
              value="Rolled Oats (45%), Honey, Almonds..."
              style={{ opacity: ingO, x: ingX, y: ingY }}
              wide
            />
            <DataChip
              label="Manufacture Date"
              value="08 / 2026"
              style={{ opacity: dateO, x: dateX, y: dateY }}
            />
          </>
        )}

        {/* Structured result */}
        <motion.div
          style={{
            opacity: prefersReduced ? 1 : dashO,
            y: prefersReduced ? 0 : dashY,
            scale: prefersReduced ? 1 : dashScale,
          }}
          className="absolute z-30 w-full max-w-4xl px-4 pointer-events-none"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="md:col-span-3 bg-white/95 backdrop-blur-sm rounded-2xl border border-zinc-200 shadow-xl px-4 py-3.5 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 min-w-0">
                <div className="h-10 w-10 rounded-xl bg-civic-success/10 flex items-center justify-center flex-shrink-0">
                  <ShieldCheck className="w-5 h-5 text-civic-success" />
                </div>
                <div className="min-w-0">
                  <p className="text-[10px] font-semibold text-civic-secondary uppercase tracking-wider">
                    Legal Metrology Compliance
                  </p>
                  <p className="text-lg font-bold text-civic-text">
                    COMPLIANT
                  </p>
                </div>
              </div>
              <span className="flex-shrink-0 text-[11px] bg-civic-success/10 text-civic-success px-2.5 py-1.5 rounded-full font-semibold border border-civic-success/20">
                5 / 5 Found
              </span>
            </div>

            <div className="bg-white/95 backdrop-blur-sm rounded-2xl border border-zinc-200 shadow-lg p-4">
              <p className="text-[10px] font-bold text-civic-secondary uppercase tracking-wider mb-2.5">
                Product
              </p>
              <div className="space-y-1.5">
                <InfoRow label="Name" value="Oats & Honey Granola" />
                <InfoRow label="Quantity" value="200 g" />
                <InfoRow label="MRP" value="₹ 120.00" />
              </div>
            </div>

            <div className="bg-white/95 backdrop-blur-sm rounded-2xl border border-zinc-200 shadow-lg p-4">
              <p className="text-[10px] font-bold text-civic-secondary uppercase tracking-wider mb-2.5">
                Mandatory Declarations
              </p>
              <div className="space-y-1.5">
                {[
                  "Manufacturer",
                  "Net Quantity",
                  "Manufacture Date",
                  "MRP",
                  "Consumer Care",
                ].map((label) => (
                  <div key={label} className="flex items-center gap-1.5 text-xs">
                    <CheckCircle2 className="w-3 h-3 text-civic-success flex-shrink-0" />
                    <span className="text-civic-text">{label}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white/95 backdrop-blur-sm rounded-2xl border border-zinc-200 shadow-lg p-4">
              <p className="text-[10px] font-bold text-civic-secondary uppercase tracking-wider mb-2.5">
                Label Extraction
              </p>
              <div className="flex flex-wrap gap-1.5 mb-2.5">
                {["Oats", "Honey", "Almonds"].map((item) => (
                  <span
                    key={item}
                    className="text-[10px] px-2 py-0.5 bg-civic-accent text-civic-primary rounded-full font-medium"
                  >
                    {item}
                  </span>
                ))}
              </div>
              <p className="text-[10px] text-civic-secondary flex items-center gap-1">
                <ScanLine className="w-3 h-3" />
                Extracted from label
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          style={{
            opacity: prefersReduced ? 0 : ctaO,
            y: prefersReduced ? 0 : ctaY,
          }}
          className="absolute bottom-7 left-0 right-0 flex flex-col items-center z-40"
        >
          <p className="text-xs text-civic-secondary mb-2.5">
            Ready to check a real product?
          </p>
          <button
            onClick={onStart}
            className="flex items-center gap-2 bg-civic-primary text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-lg hover:bg-civic-primary/90 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-civic-primary"
          >
            Scan a product <ArrowRight className="w-4 h-4" />
          </button>
        </motion.div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Small helpers
// ──────────────────────────────────────────────────────────────────────────────
function DataChip({
  label,
  value,
  style,
  wide = false,
}: {
  label: string;
  value: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  style: any;
  wide?: boolean;
}) {
  return (
    <motion.div
      style={style}
      className={`absolute z-20 bg-white px-3 py-2 rounded-lg shadow-lg border border-zinc-200 flex flex-col pointer-events-none ${
        wide ? "max-w-[180px]" : ""
      }`}
    >
      <span className="text-[9px] font-bold text-civic-secondary uppercase tracking-wider mb-0.5">
        {label}
      </span>
      <span className="text-sm font-semibold text-civic-text leading-tight">
        {value}
      </span>
    </motion.div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[9px] text-civic-muted">{label}</p>
      <p className="text-xs font-medium text-civic-text">{value}</p>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Compact hero
// ──────────────────────────────────────────────────────────────────────────────
function HeroSection({ onStart }: HomeProps) {
  return (
    <section className="px-4 pt-16 sm:pt-20 pb-10 sm:pb-12 bg-civic-bg">
      <div className="max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-[1.15fr_0.85fr] items-center gap-10 lg:gap-14">
          <div className="text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-civic-primary/20 bg-civic-accent/60 text-civic-primary text-xs font-semibold mb-5">
              <ScanLine className="w-3.5 h-3.5" />
              Label Intelligence · Compliance Verification
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-[3.8rem] font-bold tracking-tight text-civic-text leading-[1.04] mb-5 max-w-3xl">
              Know what the label says.
              <span className="block text-civic-primary">
                Know what it requires.
              </span>
            </h1>

            <p className="text-base sm:text-lg text-civic-secondary max-w-2xl mb-7 leading-relaxed">
              NIVAR analyses packaged commodity labels, extracts mandatory
              declarations, and verifies Legal Metrology compliance
              automatically.
            </p>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={onStart}
                className="flex items-center gap-2 bg-civic-primary text-white px-6 py-3 rounded-xl text-sm font-semibold shadow-md hover:bg-civic-primary/90 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-civic-primary"
              >
                Scan a product <ArrowRight className="w-4 h-4" />
              </button>

              <a
                href="#story"
                className="inline-flex items-center gap-2 px-4 py-3 rounded-xl border border-zinc-200 bg-white text-civic-secondary hover:text-civic-text hover:border-zinc-300 font-medium text-sm transition-colors"
              >
                See how it works
                <ArrowRight className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

          <div className="hidden lg:block">
            <div className="bg-white rounded-2xl border border-zinc-200 shadow-sm p-5">
              <div className="flex items-center justify-between pb-4 border-b border-zinc-100">
                <div>
                  <p className="text-[10px] uppercase tracking-wider font-bold text-civic-secondary">
                    What NIVAR checks
                  </p>
                  <p className="text-sm font-semibold text-civic-text mt-1">
                    Mandatory label declarations
                  </p>
                </div>
                <div className="h-9 w-9 rounded-xl bg-civic-accent flex items-center justify-center">
                  <ShieldCheck className="w-4 h-4 text-civic-primary" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2.5 pt-4">
                {[
                  "Manufacturer / Packer",
                  "Net Quantity",
                  "Manufacture Date",
                  "MRP",
                  "Consumer Care",
                  "Evidence & Confidence",
                ].map((item) => (
                  <div
                    key={item}
                    className="flex items-start gap-2 rounded-xl bg-civic-bg px-3 py-2.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-civic-success mt-0.5 flex-shrink-0" />
                    <span className="text-[11px] font-medium text-civic-text leading-snug">
                      {item}
                    </span>
                  </div>
                ))}
              </div>

              <div className="mt-4 rounded-xl border border-amber-200/70 bg-amber-50/60 px-3 py-2.5 flex gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600 mt-0.5 flex-shrink-0" />
                <p className="text-[10px] leading-relaxed text-civic-secondary">
                  Automated first-pass verification. Final legal
                  interpretation remains with the responsible authority.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-9 pt-5 border-t border-zinc-200/80 flex flex-wrap gap-x-7 gap-y-2.5 text-xs text-civic-muted">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-civic-success" />
            Legal Metrology (PC) Rules 2011
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-civic-success" />
            Computer Vision + OCR
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-civic-success" />
            Evidence-backed results
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-civic-success" />
            Consumer-friendly output
          </span>
        </div>
      </div>
    </section>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Main export
// ──────────────────────────────────────────────────────────────────────────────
export default function Home({ onStart }: HomeProps) {
  return (
    <div>
      <HeroSection onStart={onStart} />

      <div
        id="story"
        className="flex items-center justify-center py-5 sm:py-6 px-4"
      >
        <div className="h-px flex-1 bg-zinc-200 max-w-xs" />
        <span className="px-4 text-[10px] text-civic-muted uppercase tracking-[0.2em] font-semibold">
          How it works
        </span>
        <div className="h-px flex-1 bg-zinc-200 max-w-xs" />
      </div>

      <StorySection onStart={onStart} />
    </div>
  );
}
