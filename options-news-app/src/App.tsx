import React, { useState, useEffect } from "react";
import { TickerForm } from "./components/TickerForm";
import { fetchMultiSnapshot } from "./api/client";
import type { SymbolSnapshot } from "./types";
import { SymbolSummaryTable } from "./components/SymbolSummaryTable";
import { SymbolDetailPanel } from "./components/SymbolDetailPanel";

const App: React.FC = () => {
  const [snapshots, setSnapshots] = useState<SymbolSnapshot[]>([]);
  const [selected, setSelected] = useState<SymbolSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (params: {
    tickers: string[];
    side: "calls" | "puts" | "both";
    limit: number;
    newsCount: number;
    includePressReleases: boolean;
  }) => {
    setLoading(true);
    setError(null);

    try {
      const result = await fetchMultiSnapshot({
        tickers: params.tickers,
        side: params.side,
        limit: params.limit,
        news_count: params.newsCount,
        include_press_releases: params.includePressReleases,
      });

      setSnapshots(result);
      setSelected(result[0] ?? null); // auto-select first
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to fetch data");
      setSnapshots([]);
      setSelected(null);
    } finally {
      setLoading(false);
    }
  };

  // Keep selected in sync if data changes
  useEffect(() => {
    if (!snapshots.length) {
      setSelected(null);
      return;
    }
    if (selected) {
      const match = snapshots.find((s) => s.ticker === selected.ticker);
      if (match) {
        setSelected(match);
        return;
      }
    }
    setSelected(snapshots[0]);
  }, [selected, snapshots]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950">
        <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            Options &amp; News Multi-Symbol Dashboard
          </h1>
          <p className="text-xs text-slate-400">
            Scan 20+ tickers: options flow + news in one place.
          </p>
        </div>
      </header>

      <main className="mx-auto px-4 py-6 space-y-4">
        <TickerForm onSearch={handleSearch} loading={loading} />
        {error && (
          <div className="text-sm text-red-300 bg-red-900/40 border border-red-700 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        {loading && (
          <div className="text-sm text-slate-300">
            Fetching data… this may take a few seconds.
          </div>
        )}
        <div className="grid grid-cols-[38%_62%] gap-4">
          {!loading && snapshots.length > 0 && (
            <>
              <SymbolSummaryTable
                snapshots={snapshots}
                selectedTicker={selected?.ticker}
                onSelect={setSelected}
              />
              <SymbolDetailPanel snapshot={selected} />
            </>
          )}
        </div>
      </main >
    </div >
  );
};

export default App;
