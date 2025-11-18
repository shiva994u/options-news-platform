// src/components/NewsImpactTable.tsx
import React from "react";
import type { ArticleImpactRow } from "../types";

interface Props {
    rows: ArticleImpactRow[];
    overall: "Bullish" | "Bearish" | "Neutral";
}

const impactBadgeClass = (impact: string) => {
    switch (impact) {
        case "Bullish":
            return "text-emerald-300";
        case "Bearish":
            return "text-amber-300";
        default:
            return "text-slate-200";
    }
};

export const NewsImpactTable: React.FC<Props> = ({ rows, overall }) => {
    return (
        <div className="border border-slate-800 rounded-2xl bg-slate-900/80 p-4 text-sm space-y-3">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-xl">📊</span>
                    <div>
                        <div className="font-semibold text-slate-100">
                            Expected Impact (Article)
                        </div>
                        <div className="text-xs text-slate-400">
                            Overall:{" "}
                            <span className={impactBadgeClass(overall)}>{overall}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="min-w-full text-xs text-slate-200">
                    <thead className="border-b border-slate-700">
                        <tr>
                            <th className="text-left py-2 pr-4 font-medium">Factor</th>
                            <th className="text-left py-2 pr-4 font-medium">Impact</th>
                            <th className="text-left py-2 font-medium">Why</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((row, idx) => (
                            <tr
                                key={idx}
                                className="border-b border-slate-800 last:border-b-0"
                            >
                                <td className="py-2 pr-4 align-top whitespace-nowrap">
                                    {row.factor}
                                </td>
                                <td className="py-2 pr-4 align-top whitespace-nowrap">
                                    <span className={impactBadgeClass(row.impact)}>
                                        {row.impact}
                                    </span>
                                </td>
                                <td className="py-2 align-top text-slate-300">
                                    {row.reason}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
