import React from "react";
import type { SymbolSnapshot, OptionContract } from "../types";

interface SymbolSummaryTableProps {
  snapshots: SymbolSnapshot[];
  selectedTicker?: string;
  onSelect: (snapshot: SymbolSnapshot | null) => void;
}

function computeTotals(contracts: OptionContract[] | undefined) {
  if (!contracts || contracts.length === 0) return { volume: 0, oi: 0 };
  return contracts.reduce(
    (acc, c) => {
      acc.volume += c.volume || 0;
      acc.oi += c.openInterest || 0;
      return acc;
    },
    { volume: 0, oi: 0 }
  );
}

export const SymbolSummaryTable: React.FC<SymbolSummaryTableProps> = ({
  snapshots,
  selectedTicker,
  onSelect,
}) => {

  const formatInt = (value: number | null | undefined) =>
    value != null ? value.toLocaleString() : "—";

  if (!snapshots || snapshots.length === 0) {
    return (
      <div className="border border-slate-800 rounded-2xl bg-slate-900/70 p-3 text-sm text-slate-400">
        No data yet. Fetch some tickers to see the summary.
      </div>
    );
  }

  return (
    <div className="border border-slate-800 rounded-2xl bg-slate-900/80 p-3 h-[70vh] flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-semibold text-slate-100">
          Symbols overview
        </div>
        <div className="text-[11px] text-slate-500">
          {snapshots.length} tickers
        </div>
      </div>

      <div className="overflow-auto rounded-lg border border-slate-800/70">
        <table className="min-w-full text-[11px] text-slate-200">
          <thead className="bg-slate-950/70 sticky top-0 z-10">
            <tr>
              <th className="text-left px-3 py-2 font-medium">Ticker</th>
              <th className="text-right px-3 py-2 font-medium">Price</th>
              <th className="text-right px-3 py-2 font-medium">Total Calls</th>
              <th className="text-right px-3 py-2 font-medium">Total Puts</th>
              <th className="text-right px-3 py-2 font-medium">P/C ratio</th>
              <th className="text-center px-3 py-2 font-medium">Volume</th>
              <th className="text-center px-3 py-2 font-medium">Volume%</th>
              <th className="text-center px-3 py-2 font-medium">Earning Date</th>
            </tr>
          </thead>
          <tbody>
            {snapshots.map((snap) => {
              const opt = snap.options;
              let volDeltaPct = null;
              const callTotals = computeTotals(opt?.calls);
              const putTotals = computeTotals(opt?.puts);
              const pcr =
                (callTotals.volume + callTotals.oi) > 0
                  ? (putTotals.volume + putTotals.oi) / (callTotals.volume + callTotals.oi)
                  : null;

              if (opt != null && opt.avg_volume_3m && opt.volume) {
                volDeltaPct = ((opt.volume - opt.avg_volume_3m) / opt.avg_volume_3m) * 100;
              }

              const isSelected = snap.ticker === selectedTicker;

              let pcrClass = "text-slate-200";
              if (pcr != null) {
                if (pcr < 0.7) pcrClass = "text-emerald-400";
                else if (pcr > 1.3) pcrClass = "text-rose-400";
              }

              return (
                <tr
                  key={snap.ticker}
                  className={
                    "cursor-pointer border-t border-slate-800/70 hover:bg-slate-800/60 " +
                    (isSelected ? "bg-slate-800/80" : "")
                  }
                  onClick={() => onSelect(snap)}
                >
                  <td className="px-3 py-2 text-left font-semibold">
                    {snap.ticker}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {opt?.underlying_price != null
                      ? `$${opt.underlying_price.toFixed(2)}`
                      : "—"}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {(callTotals.volume + callTotals.oi).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {(putTotals.volume + putTotals.oi).toLocaleString()}
                  </td>
                  <td className={`px-3 py-2 text-right ${pcrClass}`}>
                    {pcr != null ? pcr.toFixed(2) : "—"}
                  </td>
                  <td className="px-3 py-2 text-center text-slate-300">
                    {formatInt(opt?.volume)}
                  </td>
                  <td className="px-3 py-2 text-center text-slate-300">
                    {parseInt((volDeltaPct || 0).toString())}%
                  </td>
                  <td className="px-3 py-2 text-center text-slate-300">
                    {opt?.earnings_date || "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-2 text-[11px] text-slate-500">
        Tip: click a row to see full details on the right.
      </div>
    </div>
  );
};
