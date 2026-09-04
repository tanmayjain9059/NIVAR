import { useRef } from "react";
import {
  motion,
  useScroll,
  useTransform,
  useReducedMotion,
} from "framer-motion";
import { ArrowRight, CheckCircle2, AlertTriangle, ScanLine } from "lucide-react";

interface HomeProps {
  onStart: () => void;
}

// ──────────────────────────────────────────────────────────────────────────────
// Scroll-driven label-extraction animation
// ──────────────────────────────────────────────────────────────────────────────
function StorySection({ onStart }: HomeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const prefersReduced = useReducedMotion();

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Package focus / scale-in
  const pkgScale = useTransform(scrollYProgress, [0, 0.12], [0.85, 1]);
  const pkgY = useTransform(scrollYProgress, [0, 0.1, 0.55, 0.9], [0, 0, -60, -160]);
  const pkgOpacity = useTransform(scrollYProgress, [0, 0.75, 0.9], [1, 1, 0]);

  // Scanning beam progress line
  const scanProgress = useTransform(scrollYProgress, [0.1, 0.45], [0, 100]);

  // Extraction fragments (opacity + offset)
  const mrpO = useTransform(scrollYProgress, [0.18, 0.28, 0.75], [0, 1, 0]);
  const mrpX = useTransform(scrollYProgress, [0.18, 0.28], [0, -170]);
  const mrpY2 = useTransform(scrollYProgress, [0.18, 0.28], [10, -90]);

  const qtyO = useTransform(scrollYProgress, [0.24, 0.34, 0.75], [0, 1, 0]);
  const qtyX = useTransform(scrollYProgress, [0.24, 0.34], [0, -190]);
  const qtyY2 = useTransform(scrollYProgress, [0.24, 0.34], [10, 60]);

  const mfgO = useTransform(scrollYProgress, [0.3, 0.4, 0.75], [0, 1, 0]);
  const mfgX = useTransform(scrollYProgress, [0.3, 0.4], [0, 190]);
  const mfgY2 = useTransform(scrollYProgress, [0.3, 0.4], [10, -70]);

  const ingO = useTransform(scrollYProgress, [0.36, 0.46, 0.75], [0, 1, 0]);
  const ingX = useTransform(scrollYProgress, [0.36, 0.46], [0, 175]);
  const ingY2 = useTransform(scrollYProgress, [0.36, 0.46], [10, 80]);

  const dateO = useTransform(scrollYProgress, [0.42, 0.52, 0.75], [0, 1, 0]);
  const dateX = useTransform(scrollYProgress, [0.42, 0.52], [0, -160]);
  const dateY2 = useTransform(scrollYProgress, [0.42, 0.52], [10, 100]);

  // Structured dashboard fade-in
  const dashO = useTransform(scrollYProgress, [0.65, 0.8], [0, 1]);
  const dashY2 = useTransform(scrollYProgress, [0.65, 0.8], [60, 0]);
  const dashScale = useTransform(scrollYProgress, [0.65, 0.8], [0.96, 1]);

  // CTA section
  const ctaO = useTransform(scrollYProgress, [0.85, 0.95], [0, 1]);
  const ctaY2 = useTransform(scrollYProgress, [0.85, 0.95], [30, 0]);

  return (
    <div ref={containerRef} className="relative h-[500vh]">
      <div className="sticky top-0 h-screen flex items-center justify-center overflow-hidden bg-civic-bg">
        {/* Subtle dot grid */}
        <div className="absolute inset-0 bg-[radial-gradient(#b0b8ba_1px,transparent_1px)] [background-size:24px_24px] opacity-40 pointer-events-none" />

        {/* Ambient glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full bg-civic-primary/5 blur-3xl pointer-events-none" />

        {/* ── Fictional Package ── */}
        <motion.div
          style={{
            scale: prefersReduced ? 1 : pkgScale,
            y: prefersReduced ? 0 : pkgY,
            opacity: prefersReduced ? 1 : pkgOpacity,
          }}
          className="relative z-10 w-52 h-72 sm:w-64 sm:h-80 bg-white rounded-2xl shadow-2xl border border-zinc-200 flex flex-col overflow-hidden select-none"
        >
          {/* Product graphic header */}
          <div className="flex-shrink-0 h-28 bg-gradient-to-br from-civic-primary/10 to-civic-accent flex items-center justify-center relative overflow-hidden">
            <div className="absolute top-2 right-2 text-[9px] text-civic-primary/40 font-mono">FICTIONAL PRODUCT</div>
            <span className="text-civic-primary font-extrabold text-2xl tracking-tighter z-10">OatBites</span>
          </div>

          {/* Label body */}
          <div className="flex-1 p-3 flex flex-col gap-1.5">
            <div className="text-[11px] font-semibold text-civic-text">Oats & Honey Granola</div>
            <div className="text-[10px] text-civic-secondary">Net Qty: 200 g</div>
            <div className="text-[10px] text-civic-secondary">MRP: ₹120.00 (incl. taxes)</div>
            <div className="mt-auto pt-2 border-t border-zinc-100 text-[8.5px] text-civic-muted leading-relaxed">
              Mfg: Example Foods Pvt. Ltd., Plot 42, Food Park, Bangalore<br />
              Mfg: 08/2026 &nbsp;|&nbsp; Exp: 07/2027
            </div>
          </div>

          {/* Animated scan beam */}
          <motion.div
            style={{ top: prefersReduced ? "50%" : useTransform(scanProgress, (v) => `${v}%`) }}
            className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-civic-primary to-transparent opacity-70 shadow-[0_0_8px_rgba(17,94,89,0.6)] z-20 pointer-events-none"
          />
        </motion.div>

        {/* ── Extracted Information Fragments ── */}
        {!prefersReduced && (
          <>
            <DataChip
              label="Maximum Retail Price"
              value="₹ 120.00"
              style={{ opacity: mrpO, x: mrpX, y: mrpY2 }}
            />
            <DataChip
              label="Net Quantity"
              value="200 g"
              style={{ opacity: qtyO, x: qtyX, y: qtyY2 }}
            />
            <DataChip
              label="Manufacturer"
              value="Example Foods Pvt. Ltd."
              style={{ opacity: mfgO, x: mfgX, y: mfgY2 }}
              wide
            />
            <DataChip
              label="Ingredients"
              value="Rolled Oats (45%), Honey, Almonds..."
              style={{ opacity: ingO, x: ingX, y: ingY2 }}
              wide
            />
            <DataChip
              label="Manufacture Date"
              value="08 / 2026"
              style={{ opacity: dateO, x: dateX, y: dateY2 }}
            />
          </>
        )}

        {/* ── Structured Dashboard (reorganised) ── */}
        <motion.div
          style={{
            opacity: prefersReduced ? 1 : dashO,
            y: prefersReduced ? 0 : dashY2,
            scale: prefersReduced ? 1 : dashScale,
          }}
          className="absolute z-30 w-full max-w-3xl px-4 pointer-events-none"
        >
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Compliance status — full width */}
            <div className="sm:col-span-3 bg-white/90 backdrop-blur-sm rounded-xl border border-zinc-200 shadow-xl p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-civic-success/10 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-5 h-5 text-civic-success" />
                </div>
                <div>
                  <p className="text-[11px] font-medium text-civic-secondary uppercase tracking-wider">Legal Metrology</p>
                  <p className="text-xl font-bold text-civic-text">COMPLIANT</p>
                </div>
              </div>
              <span className="text-xs bg-civic-success/10 text-civic-success px-3 py-1.5 rounded-full font-semibold border border-civic-success/20">
                5 / 5 Declarations Found
              </span>
            </div>

            {/* Product info */}
            <div className="bg-white/90 backdrop-blur-sm rounded-xl border border-zinc-200 shadow-lg p-4">
              <p className="text-[10px] font-bold text-civic-secondary uppercase tracking-wider mb-3">Product</p>
              <div className="space-y-2">
                <InfoRow label="Name" value="Oats & Honey Granola" />
                <InfoRow label="Quantity" value="200 g" />
                <InfoRow label="MRP" value="₹ 120.00" />
              </div>
            </div>

            {/* Compliance checks */}
            <div className="bg-white/90 backdrop-blur-sm rounded-xl border border-zinc-200 shadow-lg p-4">
              <p className="text-[10px] font-bold text-civic-secondary uppercase tracking-wider mb-3">Declarations</p>
              <div className="space-y-1.5">
                {[
                  { label: "Manufacturer", ok: true },
                  { label: "Net Quantity", ok: true },
                  { label: "Manufacture Date", ok: true },
                  { label: "MRP", ok: true },
                  { label: "Country of Origin", ok: false },
                ].map(({ label, ok }) => (
                  <div key={label} className="flex items-center gap-1.5 text-xs">
                    {ok
                      ? <CheckCircle2 className="w-3 h-3 text-civic-success flex-shrink-0" />
                      : <AlertTriangle className="w-3 h-3 text-amber-500 flex-shrink-0" />}
                    <span className="text-civic-text">{label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Food info */}
            <div className="bg-white/90 backdrop-blur-sm rounded-xl border border-zinc-200 shadow-lg p-4">
              <p className="text-[10px] font-bold text-civic-secondary uppercase tracking-wider mb-3">Food Analysis</p>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {["Oats", "Honey", "Almonds"].map((i) => (
                  <span key={i} className="text-[10px] px-2 py-0.5 bg-civic-accent text-civic-primary rounded-full font-medium">
                    {i}
                  </span>
                ))}
              </div>
              <p className="text-[10px] text-civic-secondary flex items-center gap-1">
                <ScanLine className="w-3 h-3" /> Extracted from label
              </p>
            </div>
          </div>
        </motion.div>

        {/* ── Final CTA ── */}
        <motion.div
          style={{
            opacity: prefersReduced ? 0 : ctaO,
            y: prefersReduced ? 0 : ctaY2,
          }}
          className="absolute bottom-10 left-0 right-0 flex flex-col items-center z-40"
        >
          <p className="text-sm text-civic-secondary mb-3">Now, scan your own product</p>
          <button
            onClick={onStart}
            className="flex items-center gap-2 bg-civic-primary text-white px-6 py-3 rounded-full text-sm font-semibold shadow-lg hover:bg-civic-primary/90 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-civic-primary"
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
      className={`absolute z-20 bg-white px-3 py-2 rounded-lg shadow-lg border border-zinc-200 flex flex-col pointer-events-none ${wide ? "max-w-[180px]" : ""}`}
    >
      <span className="text-[9px] font-bold text-civic-secondary uppercase tracking-wider mb-0.5">
        {label}
      </span>
      <span className="text-sm font-semibold text-civic-text leading-tight">{value}</span>
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
// Hero section above the scroll story
// ──────────────────────────────────────────────────────────────────────────────
function HeroSection({ onStart }: HomeProps) {
  return (
    <section className="pt-28 pb-16 px-4 flex flex-col items-center text-center bg-civic-bg">
      {/* Eyebrow */}
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-civic-primary/20 bg-civic-accent/60 text-civic-primary text-xs font-medium mb-6">
        <ScanLine className="w-3 h-3" />
        Label Intelligence · Compliance Verification
      </div>

      {/* Headline */}
      <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-civic-text max-w-3xl leading-[1.1] mb-5">
        Know what the label says.{" "}
        <span className="text-civic-primary">Know what it requires.</span>
      </h1>

      {/* Sub */}
      <p className="text-base sm:text-lg text-civic-secondary max-w-xl mb-10 text-balance">
        NIVAR analyses packaged commodity labels, extracts mandatory declarations, and verifies Legal Metrology compliance — automatically.
      </p>

      {/* CTAs */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <button
          onClick={onStart}
          className="flex items-center gap-2 bg-civic-primary text-white px-7 py-3 rounded-full text-sm font-semibold shadow-md hover:bg-civic-primary/90 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-civic-primary"
        >
          Scan a product <ArrowRight className="w-4 h-4" />
        </button>
        <a
          href="#story"
          className="text-sm text-civic-secondary hover:text-civic-text font-medium transition-colors underline underline-offset-4"
        >
          See how it works ↓
        </a>
      </div>

      {/* Trust strip */}
      <div className="mt-14 flex flex-wrap justify-center gap-x-8 gap-y-3 text-xs text-civic-muted">
        <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-civic-success" /> Legal Metrology (PC) Rules 2011</span>
        <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-civic-success" /> Computer Vision + OCR</span>
        <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-civic-success" /> Structured Data Output</span>
        <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-civic-success" /> Consumer-Friendly Results</span>
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

      {/* Divider label */}
      <div id="story" className="flex items-center justify-center py-8 px-4">
        <div className="h-px flex-1 bg-zinc-200 max-w-xs" />
        <span className="px-4 text-xs text-civic-muted uppercase tracking-widest font-medium">
          How it works
        </span>
        <div className="h-px flex-1 bg-zinc-200 max-w-xs" />
      </div>

      <StorySection onStart={onStart} />
    </div>
  );
}
