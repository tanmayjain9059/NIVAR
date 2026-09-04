import { useState, useRef, useCallback } from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
  Upload as UploadIcon,
  Camera,
  X,
  ArrowRight,
  AlertCircle,
  ScanLine,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";

interface UploadProps {
  onFileSelected: (file: File) => void;
}

const ACCEPTED = ["image/jpeg", "image/png", "image/webp", "image/heic"];
const MAX_SIZE_MB = 15;

export default function Upload({ onFileSelected }: UploadProps) {
  const prefersReduced = useReducedMotion();
  const inputRef = useRef<HTMLInputElement>(null);

  const [preview, setPreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = (file: File): string | null => {
    if (!ACCEPTED.includes(file.type)) {
      return "Please upload a JPG, PNG, WEBP, or HEIC image.";
    }

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `Image must be smaller than ${MAX_SIZE_MB} MB.`;
    }

    return null;
  };

  const handleFile = useCallback((file: File) => {
    const err = validate(file);

    if (err) {
      setError(err);
      return;
    }

    setError(null);
    setSelectedFile(file);

    const url = URL.createObjectURL(file);
    setPreview((previous) => {
      if (previous) URL.revokeObjectURL(previous);
      return url;
    });
  }, []);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);

    const file = e.dataTransfer.files[0];

    if (file) {
      handleFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const clearSelection = () => {
    if (preview) {
      URL.revokeObjectURL(preview);
    }

    setPreview(null);
    setSelectedFile(null);
    setError(null);

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-civic-bg px-4 py-8 sm:py-10">
      <div className="w-full max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6 sm:mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-civic-primary/20 bg-civic-accent/60 text-civic-primary text-xs font-semibold">
            <ScanLine className="w-3.5 h-3.5" />
            Product Label Scanner
          </div>

          <div className="mt-3 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-civic-text tracking-tight">
                Scan a product
              </h1>
              <p className="mt-1.5 text-sm text-civic-secondary max-w-2xl">
                Upload a clear package-label photo. NIVAR will extract the
                required declarations and check them against the configured
                Legal Metrology rules.
              </p>
            </div>

            <div className="hidden sm:flex items-center gap-2 text-xs text-civic-muted">
              <ShieldCheck className="w-4 h-4 text-civic-primary" />
              First-pass compliance verification
            </div>
          </div>
        </div>

        {/* Main workspace */}
        <div className="grid lg:grid-cols-[1fr_300px] gap-5 items-start">
          <div>
            {!preview ? (
              <motion.div
                animate={
                  prefersReduced
                    ? {}
                    : {
                        borderColor: dragging ? "#115E59" : "#d4d8d8",
                        scale: dragging ? 1.005 : 1,
                      }
                }
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => inputRef.current?.click()}
                className={`relative min-h-[330px] sm:min-h-[360px] border-2 border-dashed rounded-2xl flex flex-col items-center justify-center text-center transition-colors cursor-pointer bg-white shadow-sm px-6 py-8 ${
                  dragging
                    ? "border-civic-primary bg-civic-accent/20"
                    : "border-zinc-300 hover:border-civic-primary/50 hover:bg-zinc-50"
                }`}
              >
                <div
                  className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-4 transition-colors ${
                    dragging ? "bg-civic-accent" : "bg-zinc-100"
                  }`}
                >
                  <UploadIcon
                    className={`w-6 h-6 transition-colors ${
                      dragging ? "text-civic-primary" : "text-zinc-400"
                    }`}
                  />
                </div>

                <p className="text-sm font-semibold text-civic-text mb-1">
                  {dragging
                    ? "Drop your image here"
                    : "Drag & drop your product image"}
                </p>

                <p className="text-xs text-civic-secondary mb-5">
                  or click anywhere in this area to browse
                </p>

                <span className="inline-flex items-center gap-2 px-5 py-2.5 bg-civic-primary text-white text-xs font-semibold rounded-xl shadow-sm hover:bg-civic-primary/90 transition-colors">
                  <UploadIcon className="w-3.5 h-3.5" />
                  Choose file
                </span>

                <div className="mt-5 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-[11px] text-civic-muted">
                  <span>JPG</span>
                  <span>PNG</span>
                  <span>WEBP</span>
                  <span>HEIC</span>
                  <span>·</span>
                  <span>Up to {MAX_SIZE_MB} MB</span>
                </div>

                <div className="mt-5 pt-4 border-t border-zinc-100 w-full flex items-center justify-center gap-2 text-civic-secondary text-xs">
                  <Camera className="w-3.5 h-3.5" />
                  Mobile users can capture a label directly
                </div>
              </motion.div>
            ) : (
              <motion.div
                initial={
                  prefersReduced ? {} : { opacity: 0, scale: 0.98, y: 6 }
                }
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                className="relative rounded-2xl overflow-hidden bg-white border border-zinc-200 shadow-sm"
              >
                <div className="px-4 py-3 border-b border-zinc-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ScanLine className="w-4 h-4 text-civic-primary" />
                    <span className="text-sm font-semibold text-civic-text">
                      Selected label
                    </span>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      clearSelection();
                    }}
                    className="p-1.5 rounded-lg hover:bg-zinc-100 text-civic-secondary transition-colors"
                    aria-label="Remove image"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <div className="bg-zinc-50 flex items-center justify-center p-3 sm:p-5">
                  <img
                    src={preview}
                    alt="Selected product label"
                    className="w-full max-h-[430px] object-contain rounded-xl"
                  />
                </div>

                <div className="p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-t border-zinc-100">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-civic-text truncate">
                      {selectedFile?.name}
                    </p>
                    <p className="text-xs text-civic-muted mt-0.5">
                      {selectedFile
                        ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB`
                        : ""}
                    </p>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      clearSelection();
                    }}
                    className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl border border-zinc-200 text-xs font-semibold text-civic-secondary hover:text-civic-text hover:bg-zinc-50 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                    Change image
                  </button>
                </div>
              </motion.div>
            )}

            {/* Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-3 flex items-start gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3"
              >
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </motion.div>
            )}

            {/* Action */}
            <div className="mt-4 flex flex-col sm:flex-row gap-3">
              <button
                disabled={!selectedFile}
                onClick={() => {
                  if (selectedFile) {
                    onFileSelected(selectedFile);
                  }
                }}
                className="flex-1 flex items-center justify-center gap-2 bg-civic-primary text-white py-3.5 rounded-xl font-semibold text-sm shadow-md disabled:opacity-40 disabled:cursor-not-allowed hover:bg-civic-primary/90 transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-civic-primary"
              >
                Analyze label
                <ArrowRight className="w-4 h-4" />
              </button>

              {preview && (
                <button
                  onClick={clearSelection}
                  className="sm:w-auto px-5 py-3 rounded-xl border border-zinc-200 bg-white text-sm font-medium text-civic-secondary hover:text-civic-text hover:bg-zinc-50 transition-colors"
                >
                  Choose a different image
                </button>
              )}
            </div>
          </div>

          {/* Guidance panel */}
          <aside className="bg-white rounded-2xl border border-zinc-200 shadow-sm p-5">
            <div className="flex items-center gap-2.5 pb-4 border-b border-zinc-100">
              <div className="h-9 w-9 rounded-xl bg-civic-accent flex items-center justify-center">
                <ShieldCheck className="w-4 h-4 text-civic-primary" />
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider font-bold text-civic-secondary">
                  Best results
                </p>
                <p className="text-sm font-semibold text-civic-text">
                  Capture the label clearly
                </p>
              </div>
            </div>

            <div className="pt-4 space-y-3">
              {[
                "Keep the package inside the frame",
                "Use good lighting and avoid blur",
                "Make mandatory text readable",
                "Include the declaration area in full",
              ].map((item) => (
                <div key={item} className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-civic-success mt-0.5 flex-shrink-0" />
                  <span className="text-xs leading-relaxed text-civic-secondary">
                    {item}
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-5 pt-4 border-t border-zinc-100">
              <p className="text-[10px] uppercase tracking-wider font-bold text-civic-secondary mb-2">
                Checks include
              </p>

              <div className="flex flex-wrap gap-1.5">
                {[
                  "Manufacturer",
                  "Net Quantity",
                  "Manufacture Date",
                  "MRP",
                  "Consumer Care",
                ].map((item) => (
                  <span
                    key={item}
                    className="text-[10px] px-2 py-1 rounded-lg bg-civic-bg text-civic-text font-medium"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </aside>
        </div>

        {/* Footer note */}
        <div className="mt-5 flex items-center justify-center gap-2 text-[11px] text-civic-muted">
          <ShieldCheck className="w-3.5 h-3.5" />
          Images are processed for automated first-pass label verification.
        </div>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(",")}
        capture="environment"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];

          if (file) {
            handleFile(file);
          }
        }}
      />
    </div>
  );
}
