import { useEffect, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { analyzeImage } from "../api/analyzer";
import type { AnalyzeResponse } from "../types/analyzer";
import { ScanLine, AlertCircle } from "lucide-react";

interface ProcessingProps {
  file: File | null;
  onComplete: (result: AnalyzeResponse) => void;
}

const STEPS = [
  { id: 1, label: "Image received", detail: "Preparing label for analysis" },
  { id: 2, label: "Reading label", detail: "Applying OCR to extract text content" },
  { id: 3, label: "Identifying information", detail: "Locating declarations and product data" },
  { id: 4, label: "Checking declarations", detail: "Verifying Legal Metrology requirements" },
  { id: 5, label: "Preparing results", detail: "Structuring extracted information" },
];

const STEP_DURATION = 580;

export default function Processing({
  file,
  onComplete,
}: ProcessingProps) {
  const prefersReduced = useReducedMotion();

  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const [imageUrl] = useState<string | null>(() =>
    file ? URL.createObjectURL(file) : null
  );

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];

    STEPS.forEach((_, i) => {
      timers.push(
        setTimeout(
          () => setCurrentStep(i + 1),
          i * STEP_DURATION
        )
      );
    });

    return () => {
      timers.forEach(clearTimeout);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const runAnalysis = async () => {
      if (!file) {
        setError("No image was selected.");
        return;
      }

      try {
        setError(null);

        const result = await analyzeImage(file);

        if (!cancelled) {
          onComplete(result);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to analyze the image."
          );
        }
      }
    };

    runAnalysis();

    return () => {
      cancelled = true;
    };
  }, [file, onComplete]);

  const progress = Math.min(
    100,
    (currentStep / STEPS.length) * 100
  );

  if (error) {
    return (
      <div className="min-h-[calc(100vh-3.5rem)] pt-14 flex items-center justify-center px-4 bg-civic-bg">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-2xl border border-red-200 shadow-sm p-8 text-center">
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-red-50 flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-red-500" />
            </div>

            <h2 className="text-lg font-semibold text-civic-text mb-2">
              Analysis failed
            </h2>

            <p className="text-sm text-civic-secondary mb-6">
              {error}
            </p>

            <button
              onClick={() => window.location.reload()}
              className="px-5 py-2.5 bg-civic-primary text-white rounded-full text-sm font-semibold hover:bg-civic-primary/90 transition-colors"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] pt-14 flex items-center justify-center px-4 bg-civic-bg">
      <div className="w-full max-w-md">
        <div className="relative mb-8 rounded-2xl overflow-hidden bg-white border border-zinc-200 shadow-md h-52 flex items-center justify-center">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt="Uploaded product label being analysed"
              className="h-full w-full object-contain bg-zinc-50"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-civic-accent to-white flex items-center justify-center">
              <ScanLine className="w-12 h-12 text-civic-primary/30" />
            </div>
          )}

          <div className="absolute inset-0 bg-civic-primary/5" />

          {!prefersReduced && (
            <motion.div
              className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-civic-primary to-transparent shadow-[0_0_10px_rgba(17,94,89,0.5)]"
              animate={{ top: ["0%", "100%", "0%"] }}
              transition={{
                duration: 2.2,
                ease: "linear",
                repeat: Infinity,
              }}
            />
          )}

          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-civic-primary/80 to-transparent px-4 py-3">
            <p className="text-white text-xs font-medium flex items-center gap-1.5">
              <ScanLine className="w-3 h-3 animate-pulse" />
              Analysing label…
            </p>
          </div>
        </div>

        <div className="h-1 bg-zinc-200 rounded-full overflow-hidden mb-6">
          <motion.div
            className="h-full bg-civic-primary rounded-full"
            animate={{ width: `${progress}%` }}
            transition={{
              ease: "easeOut",
              duration: 0.5,
            }}
          />
        </div>

        <div className="space-y-3">
          <AnimatePresence>
            {STEPS.map((step, i) => {
              const done = currentStep > i;
              const active = currentStep === i + 1;
              const pending = currentStep < i + 1;

              return (
                <motion.div
                  key={step.id}
                  initial={
                    prefersReduced
                      ? {}
                      : { opacity: 0, x: -10 }
                  }
                  animate={{
                    opacity: pending ? 0.35 : 1,
                    x: 0,
                  }}
                  transition={{
                    delay: i * 0.08,
                    duration: 0.3,
                  }}
                  className="flex items-start gap-3"
                >
                  <div
                    className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 text-[10px] font-bold transition-colors ${
                      done
                        ? "bg-civic-success text-white"
                        : active
                          ? "bg-civic-primary text-white"
                          : "bg-zinc-200 text-civic-muted"
                    }`}
                  >
                    {done ? "✓" : step.id}
                  </div>

                  <div>
                    <p
                      className={`text-sm font-medium transition-colors ${
                        active
                          ? "text-civic-primary"
                          : done
                            ? "text-civic-text"
                            : "text-civic-muted"
                      }`}
                    >
                      {step.label}
                    </p>

                    {active && (
                      <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-xs text-civic-secondary mt-0.5"
                      >
                        {step.detail}
                      </motion.p>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        <p className="mt-8 text-[10px] text-civic-muted text-center leading-relaxed">
          Visual steps are a UI representation of the analysis process.
        </p>
      </div>
    </div>
  );
}