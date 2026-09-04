import { useState, useRef, useCallback } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Upload as UploadIcon, Camera, X, ArrowRight, AlertCircle } from "lucide-react";

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
    if (!ACCEPTED.includes(file.type)) return "Please upload a JPG, PNG, WEBP, or HEIC image.";
    if (file.size > MAX_SIZE_MB * 1024 * 1024) return `Image must be smaller than ${MAX_SIZE_MB} MB.`;
    return null;
  };

  const handleFile = useCallback((file: File) => {
    const err = validate(file);
    if (err) { setError(err); return; }
    setError(null);
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreview(url);
  }, []);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setDragging(true); };
  const handleDragLeave = () => setDragging(false);

  const clearSelection = () => {
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    setSelectedFile(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] pt-14 flex items-center justify-center px-4 py-10 bg-civic-bg">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-civic-text tracking-tight mb-2">Scan a product</h1>
          <p className="text-civic-secondary text-sm">
            Upload a clear photo of the packaged product label. All sides welcome.
          </p>
        </div>

        {/* Drop zone / preview */}
        {!preview ? (
          <motion.div
            animate={prefersReduced ? {} : { borderColor: dragging ? "#115E59" : "#d4d8d8" }}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`relative border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center text-center transition-colors cursor-pointer bg-white shadow-sm ${
              dragging ? "border-civic-primary bg-civic-accent/20" : "border-zinc-300 hover:border-civic-primary/50 hover:bg-zinc-50"
            }`}
            onClick={() => inputRef.current?.click()}
          >
            <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-5 transition-colors ${dragging ? "bg-civic-accent" : "bg-zinc-100"}`}>
              <UploadIcon className={`w-7 h-7 transition-colors ${dragging ? "text-civic-primary" : "text-zinc-400"}`} />
            </div>
            <p className="text-sm font-semibold text-civic-text mb-1">
              {dragging ? "Drop to upload" : "Drag & drop your image here"}
            </p>
            <p className="text-xs text-civic-secondary mb-5">or click to browse files</p>
            <span className="px-4 py-2 bg-civic-primary text-white text-xs font-semibold rounded-full hover:bg-civic-primary/90 transition-colors">
              Choose file
            </span>
            <p className="text-[11px] text-civic-muted mt-4">JPG, PNG, WEBP up to {MAX_SIZE_MB} MB</p>

            {/* Mobile camera hint */}
            <div className="mt-6 flex items-center gap-2 text-civic-secondary text-xs border-t border-zinc-100 pt-4 w-full justify-center">
              <Camera className="w-3.5 h-3.5" />
              On mobile, you can use your camera directly
            </div>
          </motion.div>
        ) : (
          /* Image preview */
          <motion.div
            initial={prefersReduced ? {} : { opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.25 }}
            className="relative rounded-2xl overflow-hidden bg-white border border-zinc-200 shadow-sm"
          >
            <img
              src={preview}
              alt="Selected product label"
              className="w-full max-h-96 object-contain bg-zinc-50"
            />
            <div className="p-4 flex items-center justify-between border-t border-zinc-100">
              <div className="min-w-0">
                <p className="text-sm font-medium text-civic-text truncate">{selectedFile?.name}</p>
                <p className="text-xs text-civic-muted">
                  {selectedFile ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB` : ""}
                </p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); clearSelection(); }}
                className="ml-3 p-1.5 rounded-full hover:bg-zinc-100 text-civic-secondary flex-shrink-0"
                aria-label="Remove image"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}

        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-3 flex items-start gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            {error}
          </motion.div>
        )}

        {/* Hidden file input */}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED.join(",")}
          capture="environment"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />

        {/* Analyze button */}
        <div className="mt-6 flex flex-col gap-3">
          <button
            disabled={!selectedFile}
            onClick={() => { if (selectedFile) onFileSelected(selectedFile); }}
            className="w-full flex items-center justify-center gap-2 bg-civic-primary text-white py-3.5 rounded-full font-semibold text-sm shadow-md disabled:opacity-40 disabled:cursor-not-allowed hover:bg-civic-primary/90 transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-civic-primary"
          >
            Analyze label <ArrowRight className="w-4 h-4" />
          </button>
          {preview && (
            <button
              onClick={clearSelection}
              className="w-full text-sm text-civic-secondary hover:text-civic-text py-2 transition-colors"
            >
              Choose a different image
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
