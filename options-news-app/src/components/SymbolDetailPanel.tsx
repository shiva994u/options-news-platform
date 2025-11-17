import React from "react";
import type { SymbolSnapshot } from "../types";
import { OptionSummaryCard } from "./OptionSummaryCard";
import { NewsList } from "./NewsList";

interface SymbolDetailPanelProps {
  snapshot: SymbolSnapshot | null;
}

export const SymbolDetailPanel: React.FC<SymbolDetailPanelProps> = ({
  snapshot,
}) => {
  if (!snapshot) {
    return (
      <div className="border border-slate-800 rounded-2xl bg-slate-900/80 p-4 text-sm text-slate-400 flex items-center justify-center h-[70vh]">
        Select a ticker on the left to see full options and news details.
      </div>
    );
  }

  return (
    <div className="border border-slate-800 rounded-2xl bg-slate-900/80 p-4 space-y-3 h-[70vh] flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          {snapshot.error && (
            <div className="mt-1 text-xs text-amber-300">
              {snapshot.error}
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto space-y-3">
        <OptionSummaryCard ticker={snapshot.ticker} options={snapshot.options} />

        <div className="grid grid-cols-1 md:grid-cols-1 gap-3">
          <NewsList title="Press releases" items={snapshot.pressReleases} />
        </div>
      </div>
    </div>
  );
};
