import type { AnalyzeResponse } from "../types/analyzer";

const API_BASE_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

export async function analyzeImages(files: File[]): Promise<AnalyzeResponse> {
  if (!files.length) throw new Error("Select at least one product image.");
  const formData = new FormData();
  files.forEach((file) => formData.append("images", file, file.name));
  const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, { method: "POST", body: formData });
  const text = await response.text();
  let result: any = {};
  try { result = text ? JSON.parse(text) : {}; } catch { result = {}; }
  if (!response.ok) throw new Error(result?.detail || "Failed to analyze product images.");
  return result as AnalyzeResponse;
}

export const analyzeImage = (file: File) => analyzeImages([file]);
