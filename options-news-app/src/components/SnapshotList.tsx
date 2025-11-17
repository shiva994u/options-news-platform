import React from "react";
import type { SymbolSnapshot } from "../types";
import { OptionSummaryCard } from "./OptionSummaryCard";
import { NewsList } from "./NewsList";

interface SnapshotListProps {
  snapshots: SymbolSnapshot[];
}

export const SnapshotList: React.FC<SnapshotListProps> = ({ snapshots }) => {
  if (!snapshots || snapshots.length === 0) return null;

  return (
    <div className="space-y-4">
      {snapshots.map((snap) => (
        <div
          key={snap.ticker}
          className="border border-slate-800 bg-slate-900/80 rounded-2xl p-4 md:p-5 shadow-md shadow-black/40 space-y-3"
        >
          <div className="flex justify-between items-center">
            <div>
              <div className="text-lg font-semibold tracking-tight">
                {snap.ticker}
              </div>
              {snap.error && (
                <div className="mt-1 text-xs text-amber-300">
                  {snap.error}
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              <OptionSummaryCard ticker={snap.ticker} options={snap.options} />
            </div>
            <div className="space-y-3">
              <NewsList title="Press releases" items={snap.pressReleases} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
