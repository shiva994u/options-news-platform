import React from "react";
import type { AIRating } from "../types";

interface Props {
  rating?: AIRating;
}

const labelStyles: Record<AIRating["label"], string> = {
  "Strong Buy":
    "bg-emerald-900/60 border-emerald-500 text-emerald-100",
  Buy: "bg-emerald-900/40 border-emerald-500/70 text-emerald-100",
  Neutral: "bg-slate-900/60 border-slate-600 text-slate-100",
  Sell: "bg-rose-900/40 border-rose-500/70 text-rose-100",
  Avoid: "bg-rose-900/60 border-rose-500 text-rose-100",
};

export const SetupSummaryBar: React.FC<Props> = ({ rating }) => {
  if (!rating) return null;

  const style = labelStyles[rating.label] ?? labelStyles.Neutral;

  return (
    <div
      className={
        "rounded-xl px-3 py-2 mb-3 border flex flex-col gap-1 " + style
      }
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-[11px] uppercase tracking-wide opacity-80">
            Setup summary ({rating.timeframe})
          </span>
          <span className="px-2 py-[2px] rounded-full bg-black/20 text-xs font-semibold">
            {rating.label}
          </span>
        </div>
        <div className="hidden md:block text-xs opacity-80">
          Score: {rating.numeric.toFixed(2)}
        </div>
      </div>

      {rating.summary && (
        <div className="text-xs leading-snug">{rating.summary}</div>
      )}

      <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-[11px] opacity-90">
        {rating.factors.slice(0, 4).map((f, idx) => (
          <div key={idx} className="flex items-center gap-1">
            <span
              className={
                "inline-block w-2 h-2 rounded-full " +
                (f.impact === "Bullish"
                  ? "bg-emerald-400"
                  : f.impact === "Bearish"
                  ? "bg-rose-400"
                  : "bg-slate-400")
              }
            />
            <span className="font-medium">{f.name}:</span>
            <span>{f.reason}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
