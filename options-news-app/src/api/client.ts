import type {
  MultiSnapshotRequest,
  SymbolSnapshot,
  ArticleAnalysis,
} from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function fetchMultiSnapshot(
  payload: MultiSnapshotRequest
): Promise<SymbolSnapshot[]> {
  const res = await fetch(`${API_BASE_URL}/options/multi-snapshot`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error: ${res.status} ${text}`);
  }

  return res.json();
}

export async function analyzeArticle(
  ticker: string,
  url: string
): Promise<ArticleAnalysis> {
  const resp = await fetch(`${API_BASE_URL}/news/analyze-article`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker, url }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Article analysis failed: ${resp.status} ${text}`);
  }

  return resp.json();
}
