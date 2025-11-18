import React from "react";
import type { SymbolSnapshot } from "../types";
import { SymbolTabs } from "./SymbolTabs";
import { SetupSummaryBar } from "./SetupSummaryBar";


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
      
      {/* 🔑 New AI-driven summary */}
      <SetupSummaryBar rating={snapshot.aiRating} />

      <div className="mt-3 flex-1 min-h-0">
        <SymbolTabs snapshot={snapshot} />
      </div>
    </div>
  );
};
