export interface Company {
  id: number;
  symbol: string;
  name: string;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  exchange: string;
  currency: string | null;
  current_price: number | null;
}

export interface IndexQuote {
  key: string;
  name: string;
  ticker: string;
  value: number | null;
  change: number | null;
  change_pct: number | null;
}

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface HistoryResponse {
  symbol: string;
  period: string;
  interval: string;
  candles: Candle[];
}

export interface Ratios {
  symbol: string;
  source: string;
  updated_at?: string;
  pe: number | null;
  forward_pe: number | null;
  pb: number | null;
  ps: number | null;
  roe: number | null;
  roa: number | null;
  roce: number | null;
  debt_to_equity: number | null;
  current_ratio: number | null;
  quick_ratio: number | null;
  gross_margin: number | null;
  operating_margin: number | null;
  net_margin: number | null;
  revenue_growth: number | null;
  earnings_growth: number | null;
  dividend_yield: number | null;
  fcf_yield: number | null;
  eps: number | null;
  beta: number | null;
}

export interface RiskSignalItem {
  code: string;
  label: string;
  severity: number;
}

export interface Risk {
  symbol: string;
  source: string;
  score: number;
  signals: RiskSignalItem[] | Record<string, unknown>[];
}

export interface StatementResponse {
  symbol: string;
  kind: string;
  period_type: string;
  periods: string[];
  rows: Record<string, (number | null)[]>;
}

export interface NewsArticle {
  title: string;
  link: string;
  source: string | null;
  published: string | null;
  relevance?: number | null;
  summary?: string | null;
  sentiment?: string | null;
}

export interface NewsResponse {
  symbol: string;
  count: number;
  articles: NewsArticle[];
}

export interface ScreenerRow {
  symbol: string;
  name: string;
  sector: string | null;
  market_cap: number | null;
  current_price: number | null;
  pe: number | null;
  roe: number | null;
  dividend_yield: number | null;
}

export interface WatchlistRow {
  id: number;
  symbol: string;
  name: string;
  sector: string | null;
  current_price: number | null;
  market_cap: number | null;
  pe: number | null;
  roe: number | null;
  risk_score: number | null;
}

export interface Holding {
  id: number;
  symbol: string;
  name: string;
  sector: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  invested: number;
  current_value: number;
  pl: number;
  pl_pct: number | null;
}

export interface PortfolioSummary {
  invested: number;
  current_value: number;
  pl: number;
  pl_pct: number | null;
  holdings_count: number;
}

export interface SectorAllocation {
  sector: string;
  value: number;
  pct: number;
}

export interface Portfolio {
  holdings: Holding[];
  summary: PortfolioSummary;
  sector_allocation: SectorAllocation[];
}

export interface DocumentItem {
  id: number;
  filename: string;
  status: "pending" | "processing" | "ready" | "failed";
  num_pages: number | null;
  num_chunks: number;
  error: string | null;
  created_at: string;
}

export interface Citation {
  agent?: string;
  type?: string;
  marker?: number;
  chunk_id?: number;
  document_id?: number;
  filename?: string;
  page_number?: number;
  label?: string;
  snippet?: string;
  url?: string;
}

export interface AgentInfo {
  id: string;
  name: string;
  role: string;
}
