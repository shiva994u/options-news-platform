import React from "react";
import type { OptionsSnapshot, OptionContract } from "../types";

interface OptionSummaryCardProps {
  options: OptionsSnapshot | null;
  ticker: string;
}

function computeTotals(contracts: OptionContract[] | undefined) {
  if (!contracts || contracts.length === 0) {
    return { volume: 0, openInterest: 0 };
  }
  return contracts.reduce(
    (acc, c) => {
      acc.volume += c.volume || 0;
      acc.openInterest += c.openInterest || 0;
      return acc;
    },
    { volume: 0, openInterest: 0 }
  );
}

const ContractsTable: React.FC<{
  title: string;
  contracts?: OptionContract[];
}> = ({ title, contracts }) => {
  if (!contracts || contracts.length === 0) {
    return (
      <div className="text-xs text-slate-400">
        No {title.toLowerCase()} contracts.
      </div>
    );
  }

  const top = contracts.sort((a, b) => (b.openInterest || 0) - (a.openInterest || 0)).slice(0, 8);

  return (
    <div className="space-y-1">
      <div className="text-xs font-semibold text-slate-200">{title}</div>
      <table className="w-full text-[11px] text-slate-300">
        <thead className="text-slate-400">
          <tr>
            <th className="text-left py-1 pr-2">Strike</th>
            <th className="text-right py-1 px-2">Last</th>
            <th className="text-right py-1 px-2">Vol</th>
            <th className="text-right py-1 px-2">OI</th>
            <th className="text-right py-1 pl-2">IV</th>
          </tr>
        </thead>
        <tbody>
          {top.map((c) => (
            <tr key={c.contractSymbol} className="border-t border-slate-800/70">
              <td className="py-1 pr-2">
                ${c.strike}
                {c.inTheMoney && (
                  <span className="ml-1 text-[10px] px-1 rounded bg-emerald-900/60 text-emerald-300">
                    ITM
                  </span>
                )}
              </td>
              <td className="py-1 px-2 text-right">{c.lastPrice}</td>
              <td className="py-1 px-2 text-right">
                {c.volume ?? 0}
              </td>
              <td className="py-1 px-2 text-right">
                {c.openInterest ?? 0}
              </td>
              <td className="py-1 pl-2 text-right">
                {c.impliedVolatility != null
                  ? (c.impliedVolatility * 100).toFixed(1) + "%"
                  : "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export const OptionSummaryCard: React.FC<OptionSummaryCardProps> = ({
  options,
  ticker
}) => {
  if (!options) {
    return (
      <div className="border border-slate-800 rounded-xl p-3 bg-slate-950/60 text-xs text-slate-400">
        No options data available for this symbol.
      </div>
    );
  }

  const callTotals = computeTotals(options.calls);
  const putTotals = computeTotals(options.puts);
  const putCallRatio =
    callTotals.openInterest > 0 ? putTotals.openInterest / callTotals.openInterest : null;

  let sentimentLabel = "Neutral";
  let sentimentClass = "bg-slate-800 text-slate-200";
  if (putCallRatio != null) {
    if (putCallRatio < 0.7) {
      sentimentLabel = "Call-heavy (Bullish)";
      sentimentClass = "bg-emerald-900/70 text-emerald-200";
    } else if (putCallRatio > 1.3) {
      sentimentLabel = "Put-heavy (Bearish)";
      sentimentClass = "bg-rose-900/70 text-rose-200";
    }
  }

  return (
    <div className="border border-slate-800 rounded-2xl p-3 bg-slate-950/60 text-xs space-y-3">
      {/* top row: expiration + underlying + sentiment */}

      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-lg font-semibold tracking-tight">
            {ticker}
          </div>
        </div>
        <div>
          <div className="text-[11px] text-slate-400">Expiration</div>
          <div className="text-sm font-medium">
            {options.expiration ?? "N/A"}
          </div>
        </div>
        <div>
          <div className="text-[11px] text-slate-400">Underlying</div>
          <div className="text-sm font-semibold">
            {options.underlying_price != null
              ? `$${options.underlying_price.toFixed(2)}`
              : "N/A"}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg bg-slate-900/80 border border-slate-800 px-3 py-2">
            <div className="text-[11px] text-slate-400">Call OI</div>
            <div className="text-sm font-semibold">
              {callTotals.openInterest.toLocaleString()}
            </div>
            <div className="text-[11px] text-slate-500">
              Volume {callTotals.volume.toLocaleString()}
            </div>
          </div>
          <div className="rounded-lg bg-slate-900/80 border border-slate-800 px-3 py-2">
            <div className="text-[11px] text-slate-400">Put OI</div>
            <div className="text-sm font-semibold">
              {putTotals.openInterest.toLocaleString()}
            </div>
            <div className="text-[11px] text-slate-500">
              Volume {putTotals.volume.toLocaleString()}
            </div>
          </div>
          <div className="rounded-lg bg-slate-900/80 border border-slate-800 px-3 py-2">
            <div className="text-[11px] text-slate-400">
              Put/Call ratio&nbsp;
              <span
                className={`text-sm font-semibold ${putCallRatio != null && putCallRatio > 1
                  ? "text-rose-400"
                  : "text-emerald-400"
                  }`}
              >
                {putCallRatio != null ? putCallRatio.toFixed(2) : "N/A"}
              </span>
            </div>
            <div className="text-[11px] text-slate-500 py-2">
              <span className={`px-2 py-1 rounded-full text-[11px] ${sentimentClass}`}>
                {sentimentLabel}
              </span>
              &lt; 1 bullish, &gt; 1 bearish
            </div>
          </div>
        </div>
      </div>

      {/* stat tiles */}


      {/* tables */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <ContractsTable title="Calls (top by volume)" contracts={options.calls} />
        <ContractsTable title="Puts (top by volume)" contracts={options.puts} />
      </div>

      {options.note && (
        <div className="text-[11px] text-amber-300 bg-amber-900/40 border border-amber-700 rounded-lg px-2 py-1">
          {options.note}
        </div>
      )}
    </div>
  );
};
