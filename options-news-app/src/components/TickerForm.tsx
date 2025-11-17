import React, { useState } from "react";

interface TickerFormProps {
  onSearch: (params: {
    tickers: string[];
    side: "calls" | "puts" | "both";
    limit: number;
    newsCount: number;
    includePressReleases: boolean;
  }) => void;
  loading: boolean;
}

export const TickerForm: React.FC<TickerFormProps> = ({
  onSearch,
  loading,
}) => {
  const [tickerInput, setTickerInput] = useState("");
  const [side, setSide] = useState<"calls" | "puts" | "both">("both");
  const [limit, setLimit] = useState(50);
  const [newsCount, setNewsCount] = useState(3);
  const [includePR, setIncludePR] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const tickers = tickerInput
      .split(/[,\s]+/)
      .map((t) => t.trim().toUpperCase())
      .filter(Boolean);

    if (tickers.length === 0) return;

    onSearch({
      tickers,
      side,
      limit,
      newsCount,
      includePressReleases: includePR,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-slate-900/70 border border-slate-700 rounded-2xl shadow-lg shadow-slate-900/40 px-4 py-4 md:px-6 md:py-5 space-y-4"
    >
      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1">
          Tickers (comma or space separated)
        </label>
        <input
          type="text"
          className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={tickerInput}
          onChange={(e) => setTickerInput(e.target.value)}
          placeholder="AAPL, NVDA, AMGN"
        />
      </div>

      <div className="flex flex-wrap gap-4 text-xs">
        <div>
          <label className="block text-sm font-medium mb-1">Side</label>
          <select
            className="border rounded px-2 py-1 text-sm"
            value={side}
            onChange={(e) =>
              setSide(e.target.value as "calls" | "puts" | "both")
            }
          >
            <option value="both">Calls & Puts</option>
            <option value="calls">Calls only</option>
            <option value="puts">Puts only</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Contracts per side
          </label>
          <input
            type="number"
            className="border rounded px-2 py-1 text-sm w-20"
            min={1}
            max={200}
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value) || 1)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            News per ticker
          </label>
          <input
            type="number"
            className="border rounded px-2 py-1 text-sm w-20"
            min={0}
            max={10}
            value={newsCount}
            onChange={(e) => setNewsCount(Number(e.target.value) || 0)}
          />
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={includePR}
            onChange={(e) => setIncludePR(e.target.checked)}
          />
          Include press releases
        </label>

        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-900 text-sm font-medium text-white shadow shadow-blue-900/40 transition-colors"
        >
          {loading ? "Loading…" : "Fetch Snapshots"}
        </button>
      </div>

    </form>
  );
};
