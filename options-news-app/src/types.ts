export type ImpactDirection = "Bullish" | "Bearish" | "Neutral";

export interface ArticleImpactRow {
  factor: string;
  impact: ImpactDirection;
  reason: string;
}
export type FactorImpact = "Bullish" | "Bearish" | "Neutral";
export interface AIRatingFactor {
  name: string;
  impact: FactorImpact;
  score: number; // -2..+2
  reason: string;
}

export type AIRatingLabel = "Strong Buy" | "Buy" | "Neutral" | "Sell" | "Avoid";

export interface AIRating {
  label: AIRatingLabel;
  numeric: number;
  timeframe: string;
  summary: string;
  factors: AIRatingFactor[];
  source?: string;
}

export interface ArticleAnalysis {
  url: string;
  ticker?: string;
  overall: ImpactDirection;
  score: number;
  rows: ArticleImpactRow[];
  summary?: string | null;
}

export interface OptionContract {
  contractSymbol: string;
  strike: number;
  lastPrice: number;
  bid: number | null;
  ask: number | null;
  volume: number | null;
  openInterest: number | null;
  impliedVolatility: number | null;
  inTheMoney: boolean;
}

export interface OptionsSnapshot {
  ticker: string;
  expiration: string | null;
  underlying_price: number | null;
  volume: number | null;
  avg_volume_10d: number | null;
  avg_volume_3m: number | null;
  earnings_date: string | null;
  calls?: OptionContract[];
  puts?: OptionContract[];
  note?: string;
  // optional aggregate fields if you add them later
  total_call_volume?: number;
  total_put_volume?: number;
  call_put_ratio?: number;
  top_call_contract?: OptionContract | null;
  top_put_contract?: OptionContract | null;
}

export interface NewsItem {
  title: string;
  publisher: string | null;
  relativeTime?: string | null;
  link: string;
}

export interface Rating {
  label: string;
  total_score: number;
  volume_score: number;
  price_score: number;
  options_score: number;
  news_score: number;
  volume_ratio?: number | null;
  put_call_vol_ratio?: number | null;
  put_call_oi_ratio?: number | null;
  options_to_stock_vol_ratio?: number | null;
  gap_percent?: number | null;
  intraday_change_percent?: number | null;
  raw_news_score?: number;
}

export interface SymbolSnapshot {
  ticker: string;
  options: OptionsSnapshot | null;
  news: NewsItem[];
  pressReleases: NewsItem[];
  error: string | null;
  rating?: Rating; // 👈 add this
  aiRating?: AIRating;
}

export interface MultiSnapshotRequest {
  tickers: string[];
  expiration?: string | null;
  side?: "calls" | "puts" | "both";
  limit?: number;
  news_count?: number;
  include_press_releases?: boolean;
}
