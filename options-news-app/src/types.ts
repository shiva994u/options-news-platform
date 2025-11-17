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

export interface SymbolSnapshot {
  ticker: string;
  options: OptionsSnapshot | null;
  news: NewsItem[];
  pressReleases: NewsItem[];
  error: string | null;
}

export interface MultiSnapshotRequest {
  tickers: string[];
  expiration?: string | null;
  side?: "calls" | "puts" | "both";
  limit?: number;
  news_count?: number;
  include_press_releases?: boolean;
}
