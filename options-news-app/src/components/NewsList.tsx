import React from "react";
import type { NewsItem } from "../types";

interface NewsListProps {
  title: string;
  items: NewsItem[];
}

// Parse relative time like "7h ago", "23m ago", "2d ago", "2mo ago", "3 weeks ago"
function relativeTimeToHours(relativeTime?: string | null): number | null {
  if (!relativeTime) return null;

  const text = relativeTime.toLowerCase().trim();

  if (text.includes("just now")) {
    return 0;
  }

  // Extract first number + alpha token
  const match = text.match(/(\d+)\s*([a-z]+)/);
  if (!match) return null;

  const value = parseInt(match[1], 10);
  const unitToken = match[2]; // e.g. "h", "hr", "hrs", "m", "min", "d", "mo"
  if (Number.isNaN(value)) return null;

  // Use full text to distinguish "mo" (months) from "m" (minutes)
  const t = text;

  // Minutes
  if (
    t.includes("min") ||
    unitToken === "m" ||
    unitToken.startsWith("min")
  ) {
    return value / 60;
  }

  // Hours
  if (
    t.includes("hour") ||
    unitToken === "h" ||
    unitToken.indexOf("hr") >= 0 || // optional chaining for safety
    unitToken === "hrs"
  ) {
    return value;
  }

  // Days
  if (t.includes("day") || unitToken === "d") {
    return value * 24;
  }

  // Weeks
  if (t.includes("week") || unitToken.startsWith("w")) {
    return value * 7 * 24;
  }

  // Months (approx)
  if (t.includes("month") || unitToken.startsWith("mo")) {
    return value * 30 * 24;
  }

  // Years (approx)
  if (t.includes("year") || unitToken.startsWith("y")) {
    return value * 365 * 24;
  }

  // Fallback: unknown unit
  return null;
}

export const NewsList: React.FC<NewsListProps> = ({ title, items }) => {
  // Keep only articles within last 24 hours
  const filtered = items.filter((item) => {
    const hours = relativeTimeToHours(item.relativeTime);
    if (hours == null) return false; // if we can't parse, drop it
    return hours <= 24;
  });

  const count = filtered.length;

  return (
    <div className="border border-slate-800 rounded-2xl p-3 bg-slate-950/60 text-xs space-y-2 h-full">
      <div className="flex items-center justify-between mb-1">
        <div className="font-semibold text-slate-100">
          {title}{" "}
          <span className="text-[11px] text-slate-500">(last 24h)</span>
        </div>
        <div className="text-[11px] text-slate-500">
          {count} item{count !== 1 && "s"}
        </div>
      </div>

      {count === 0 && (
        <div className="text-[11px] text-slate-400">
          No {title.toLowerCase()} in the last 24 hours.
        </div>
      )}

      {filtered.map((item, idx) => (
        <div
          key={idx}
          className="pb-2 mb-2 border-b border-slate-800 last:mb-0 last:pb-0 last:border-0"
        >
          <a
            href={item.link}
            target="_blank"
            rel="noreferrer"
            className="text-slate-100 hover:text-blue-400 hover:underline"
          >
            {item.title}
          </a>
          <div className="mt-0.5 text-[11px] text-slate-400 flex flex-wrap gap-2">
            {item.publisher && <span>{item.publisher}</span>}
            {item.relativeTime && <span>• {item.relativeTime}</span>}
          </div>
        </div>
      ))}
    </div>
  );
};
