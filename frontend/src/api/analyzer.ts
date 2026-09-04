import type { AnalyzeResponse } from "../types/analyzer";

const API_BASE_URL = "http://127.0.0.1:8000";

export async function analyzeImage(
  file: File
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch(
    `${API_BASE_URL}/api/v1/analyze`,
    {
      method: "POST",
      body: formData,
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result?.detail?.message ||
      result?.detail ||
      "Failed to analyze image."
    );
  }

  return result as AnalyzeResponse;
}