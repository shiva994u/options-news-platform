import React from "react";
import type { NewsItem } from "../types";

interface NewsUrlSelectorProps {
  ticker: string;
  items: NewsItem[];
  selectedUrl: string | null;
  onChange: (url: string | null) => void;
  label?: string;
}

export const NewsUrlSelector: React.FC<NewsUrlSelectorProps> = ({
  ticker,
  items,
  selectedUrl,
  onChange,
  label = "Article",
}) => {
  if (!items || items.length === 0) {
    return (
      <div className="text-[11px] text-slate-500">
        No news available to analyze for {ticker}.
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-slate-400 whitespace-nowrap">
        {label}:
      </span>
      <select
        value={selectedUrl ?? ""}
        onChange={(e) => onChange(e.target.value || null)}
        className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-100 flex-1"
      >
        {items.map((n, i) => (
          <option key={i} value={n.link}>
            {/* title + (relativeTime) for extra context */}
            {n.title.slice(0, 90)}
            {n.relativeTime ? ` (${n.relativeTime})` : ""}
          </option>
        ))}
      </select>
    </div>
  );
};
