import { useRef, useState } from "react";
import {
  Upload as UploadIcon,
  X,
  ArrowRight,
  AlertCircle,
  ScanLine,
  ShieldCheck,
  CheckCircle2,
  Plus,
} from "lucide-react";

interface Props { onFilesSelected: (files: File[]) => void; }
const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];
const MAX = 15;
const LIMIT = 8;

export default function Upload({ onFilesSelected }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState("");

  const add = (incoming: FileList | File[]) => {
    const next = [...files];
    for (const f of Array.from(incoming)) {
      if (!ACCEPTED.includes(f.type)) {
        setError("Use JPG, PNG or WEBP images.");
        continue;
      }
      if (f.size > MAX * 1024 * 1024) {
        setError(`${f.name} is larger than ${MAX} MB.`);
        continue;
      }
      if (next.length >= LIMIT) break;
      if (!next.some((x) => x.name === f.name && x.size === f.size)) next.push(f);
    }
    setFiles(next);
    if (next.length) setError("");
  };

  const remove = (i: number) => setFiles(files.filter((_, n) => n !== i));

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-civic-bg px-4 py-8 sm:py-10">
      <div className="max-w-6xl mx-auto">
        <div className="mb-7">
          <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-civic-primary/20 bg-civic-accent text-civic-primary text-xs font-semibold">
            <ScanLine className="w-3.5 h-3.5" />Product Label Scanner
          </span>
          <h1 className="mt-3 text-3xl sm:text-4xl font-bold text-civic-text">Scan a product</h1>
          <p className="mt-2 text-sm text-civic-secondary max-w-2xl">
            Upload front, back and side photos. NIVAR fuses evidence from all images into one product-level compliance result.
          </p>
        </div>
        <div className="grid lg:grid-cols-[1fr_300px] gap-5">
          <section>
            <div onClick={() => input.current?.click()} className="min-h-[240px] border-2 border-dashed border-zinc-300 hover:border-civic-primary/60 rounded-2xl bg-white flex flex-col items-center justify-center cursor-pointer shadow-sm p-6 text-center">
              <div className="w-14 h-14 rounded-2xl bg-civic-accent flex items-center justify-center"><UploadIcon className="w-7 h-7 text-civic-primary" /></div>
              <p className="mt-4 text-sm font-semibold text-civic-text">Add product images</p>
              <p className="mt-1 text-xs text-civic-secondary">Select multiple photos at once or add more later</p>
              <span className="mt-4 inline-flex items-center gap-2 px-5 py-2.5 bg-civic-primary text-white rounded-xl text-xs font-semibold"><Plus className="w-4 h-4" />Choose images</span>
              <p className="mt-4 text-[11px] text-civic-muted">JPG · PNG · WEBP · up to 8 images · 15 MB each</p>
            </div>
            {files.length > 0 && (
              <div className="mt-4 grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {files.map((f, i) => (
                  <div key={f.name + f.size} className="bg-white border border-zinc-200 rounded-xl overflow-hidden shadow-sm">
                    <div className="relative h-40 bg-zinc-50">
                      <img src={URL.createObjectURL(f)} className="w-full h-full object-contain" alt={f.name} />
                      <button onClick={() => remove(i)} className="absolute top-2 right-2 p-1.5 rounded-lg bg-white/90 shadow text-zinc-600" aria-label="Remove image">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="p-3">
                      <p className="text-xs font-medium truncate">{f.name}</p>
                      <p className="text-[10px] text-civic-muted mt-1">{(f.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {error && <div className="mt-3 flex gap-2 p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700"><AlertCircle className="w-4 h-4 mt-0.5" />{error}</div>}
            <div className="mt-4 flex gap-3">
              <button disabled={!files.length} onClick={() => onFilesSelected(files)} className="flex-1 inline-flex items-center justify-center gap-2 bg-civic-primary text-white py-3.5 rounded-xl font-semibold text-sm disabled:opacity-40">
                Analyze {files.length || ""} image{files.length === 1 ? "" : "s"} <ArrowRight className="w-4 h-4" />
              </button>
              <button onClick={() => input.current?.click()} className="px-5 rounded-xl border bg-white text-sm font-medium"><Plus className="w-4 h-4 inline mr-1" />Add more</button>
            </div>
          </section>
          <aside className="bg-white rounded-2xl border border-zinc-200 p-5 shadow-sm">
            <div className="flex gap-3 pb-4 border-b">
              <div className="h-9 w-9 rounded-xl bg-civic-accent flex items-center justify-center"><ShieldCheck className="w-4 h-4 text-civic-primary" /></div>
              <div><p className="text-[10px] uppercase tracking-wider font-bold text-civic-secondary">Best results</p><p className="text-sm font-semibold">Use complementary views</p></div>
            </div>
            <div className="pt-4 space-y-3">
              {["Front: product name and brand", "Back: ingredients and nutrition", "Side/back: MRP, quantity and dates", "Keep text sharp and readable"].map((x) => (
                <div className="flex gap-2.5 text-xs text-civic-secondary" key={x}><CheckCircle2 className="w-4 h-4 text-civic-success flex-shrink-0" />{x}</div>
              ))}
            </div>
            <div className="mt-5 pt-4 border-t">
              <p className="text-[10px] uppercase font-bold text-civic-secondary mb-2">Core checks</p>
              <div className="flex flex-wrap gap-1.5">{["Manufacturer", "Net Quantity", "Manufacture Date", "MRP", "Consumer Care"].map((x) => <span className="text-[10px] px-2 py-1 rounded-lg bg-civic-bg" key={x}>{x}</span>)}</div>
            </div>
          </aside>
        </div>
      </div>
      <input ref={input} hidden multiple type="file" accept={ACCEPTED.join(",")} onChange={(e) => e.target.files && add(e.target.files)} />
    </div>
  );
}
