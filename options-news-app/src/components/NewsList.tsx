import React from "react";
import type { NewsItem } from "../types";

interface NewsListProps {
  title: string;
  items: NewsItem[];
}

export const NewsList: React.FC<NewsListProps> = ({ title, items }) => {
  return (
    <div className="border border-slate-800 rounded-2xl p-3 bg-slate-950/60 text-xs space-y-2 h-full">
      <div className="flex items-center justify-between mb-1">
        <div className="font-semibold text-slate-100">{title}</div>
        <div className="text-[11px] text-slate-500">
          {items.length} item{items.length !== 1 && "s"}
        </div>
      </div>

      {items.length === 0 && (
        <div className="text-[11px] text-slate-400">No {title.toLowerCase()} found.</div>
      )}

      {items.map((item, idx) => (
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
