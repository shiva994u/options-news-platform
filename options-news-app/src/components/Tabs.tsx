// src/components/Tabs.tsx
import React, { type ReactNode } from "react";

export interface TabConfig {
  id: string;
  label: string;
  content: ReactNode;
}

interface TabsProps {
  tabs: TabConfig[];
  activeId: string;
  onChange: (id: string) => void;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeId, onChange }) => {
  const activeTab = tabs.find((t) => t.id === activeId);

  return (
    <div className="flex flex-col h-full">
      {/* tab headers */}
      <div className="flex gap-2 border-b border-slate-800 text-xs">
        {tabs.map((tab) => {
          const isActive = tab.id === activeId;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onChange(tab.id)}
              className={
                "px-3 py-2 rounded-t-lg border-b-2 -mb-px transition-colors " +
                (isActive
                  ? "border-blue-500 text-slate-100 bg-slate-900"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50")
              }
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* 🔑 scrollable tab body */}
      <div className="flex-1 min-h-0 overflow-y-auto mt-3">
        {activeTab?.content}
      </div>
    </div>
  );
};
