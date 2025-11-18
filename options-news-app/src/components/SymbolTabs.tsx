// src/components/SymbolTabs.tsx
import React, { useEffect, useState } from "react";
import type { SymbolSnapshot, ArticleAnalysis } from "../types";
import { Tabs, type TabConfig } from "./Tabs";
import { OptionSummaryCard } from "./OptionSummaryCard";
import { NewsList } from "./NewsList";
import { NewsImpactTable } from "./NewsImpactTable";
import { NewsUrlSelector } from "./NewsUrlSelector";
import { analyzeArticle } from "../api/client";

interface SymbolTabsProps {
  snapshot: SymbolSnapshot;
}

export const SymbolTabs: React.FC<SymbolTabsProps> = ({ snapshot }) => {
  const [activeId, setActiveId] = useState<string>("overview");
  const [selectedNewsUrl, setSelectedNewsUrl] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<ArticleAnalysis | null>(null);
  const [loadingImpact, setLoadingImpact] = useState(false);
  const [impactError, setImpactError] = useState<string | null>(null);

  useEffect(() => {
    setActiveId("overview");
    if (snapshot.news && snapshot.news.length > 0) {
      setSelectedNewsUrl(snapshot.news[0].link);
    } else {
      setSelectedNewsUrl(null);
    }
    setAnalysis(null);
    setImpactError(null);
  }, [snapshot.ticker]);

  useEffect(() => {
    const run = async () => {
      if (activeId !== "impact" || !selectedNewsUrl) return;
      setLoadingImpact(true);
      setImpactError(null);
      try {
        const res = await analyzeArticle(snapshot.ticker, selectedNewsUrl);
        setAnalysis(res);
      } catch (err: any) {
        setImpactError(err.message ?? "Failed to analyze article");
        setAnalysis(null);
      } finally {
        setLoadingImpact(false);
      }
    };

    void run();
  }, [activeId, selectedNewsUrl, snapshot.ticker]);

  const tabs: TabConfig[] = [
    {
      id: "overview",
      label: "Overview",
      content: (
        <div className="space-y-3">
          <OptionSummaryCard options={snapshot.options} ticker={snapshot.ticker} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <NewsList title="Press releases" items={snapshot.pressReleases} />
          </div>
        </div>
      ),
    },
    {
      id: "impact",
      label: "News impact",
      content: (
        <div className="flex flex-col gap-3">
          <NewsUrlSelector
            ticker={snapshot.ticker}
            items={snapshot.news}
            selectedUrl={selectedNewsUrl}
            onChange={setSelectedNewsUrl}
            label="Article"
          />

          {loadingImpact && (
            <div className="text-xs text-slate-400">
              Analyzing article content…
            </div>
          )}
          {impactError && (
            <div className="text-xs text-rose-300">{impactError}</div>
          )}
          {analysis && !loadingImpact && (
            <NewsImpactTable
              overall={analysis.overall}
              rows={analysis.rows}
            />
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="h-full">
      <Tabs tabs={tabs} activeId={activeId} onChange={setActiveId} />
    </div>
  );
};
