import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiDelete, apiGet, apiPost, apiUpload } from "./api";
import type {
  AgentInfo,
  Company,
  DocumentItem,
  HistoryResponse,
  IndexQuote,
  NewsResponse,
  Portfolio,
  Ratios,
  Risk,
  ScreenerRow,
  StatementResponse,
  WatchlistRow,
} from "./types";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => apiGet<{ status: string; service: string; env: string }>("/api/health"),
    staleTime: 60000,
  });
}

export function useIndices() {
  return useQuery({
    queryKey: ["indices"],
    queryFn: () => apiGet<{ indices: IndexQuote[] }>("/api/market/indices"),
    refetchInterval: 60000,
  });
}

export function useCompanies(params: { search?: string; sector?: string } = {}) {
  const qs = new URLSearchParams();
  if (params.search) qs.set("search", params.search);
  if (params.sector) qs.set("sector", params.sector);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return useQuery({
    queryKey: ["companies", params],
    queryFn: () => apiGet<Company[]>(`/api/companies${suffix}`),
  });
}

export function useCompany(symbol: string) {
  return useQuery({
    queryKey: ["company", symbol],
    queryFn: () => apiGet<Company>(`/api/companies/${symbol}`),
    enabled: !!symbol,
  });
}

export function useHistory(symbol: string, period: string) {
  return useQuery({
    queryKey: ["history", symbol, period],
    queryFn: () => apiGet<HistoryResponse>(`/api/companies/${symbol}/history?period=${period}`),
    enabled: !!symbol,
  });
}

export function useRatios(symbol: string) {
  return useQuery({
    queryKey: ["ratios", symbol],
    queryFn: () => apiGet<Ratios>(`/api/companies/${symbol}/ratios`),
    enabled: !!symbol,
  });
}

export function useMultiRatios(symbols: string[]) {
  return useQueries({
    queries: symbols.map((s) => ({
      queryKey: ["ratios", s],
      queryFn: () => apiGet<Ratios>(`/api/companies/${s}/ratios`),
      enabled: !!s,
    })),
  });
}

export function useRisk(symbol: string) {
  return useQuery({
    queryKey: ["risk", symbol],
    queryFn: () => apiGet<Risk>(`/api/companies/${symbol}/risk`),
    enabled: !!symbol,
  });
}

export function useStatement(symbol: string, kind: string, periodType: string) {
  return useQuery({
    queryKey: ["statement", symbol, kind, periodType],
    queryFn: () =>
      apiGet<StatementResponse>(
        `/api/companies/${symbol}/statements/${kind}?period_type=${periodType}`
      ),
    enabled: !!symbol,
  });
}

export function useNews(symbol: string) {
  return useQuery({
    queryKey: ["news", symbol],
    queryFn: () => apiGet<NewsResponse>(`/api/news/${symbol}`),
    enabled: !!symbol,
  });
}

export interface ScreenerFilters {
  sector?: string;
  market_cap_min?: number;
  pe_min?: number;
  pe_max?: number;
  roe_min?: number;
  dividend_yield_min?: number;
  sort_by?: string;
  desc?: boolean;
}

export function useScreener(filters: ScreenerFilters) {
  const qs = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  });
  return useQuery({
    queryKey: ["screener", filters],
    queryFn: () =>
      apiGet<{ count: number; results: ScreenerRow[] }>(`/api/screener?${qs.toString()}`),
  });
}

export function useWatchlist() {
  return useQuery({
    queryKey: ["watchlist"],
    queryFn: () => apiGet<{ items: WatchlistRow[] }>("/api/watchlist"),
  });
}

export function useAddWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => apiPost("/api/watchlist", { symbol }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["watchlist"] }),
  });
}

export function useRemoveWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => apiDelete(`/api/watchlist/${symbol}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["watchlist"] }),
  });
}

export function usePortfolio() {
  return useQuery({
    queryKey: ["portfolio"],
    queryFn: () => apiGet<Portfolio>("/api/portfolio"),
  });
}

export function useAddHolding() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { symbol: string; quantity: number; avg_price: number }) =>
      apiPost<Portfolio>("/api/portfolio", payload),
    onSuccess: (data) => qc.setQueryData(["portfolio"], data),
  });
}

export function useRemoveHolding() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiDelete<Portfolio>(`/api/portfolio/${id}`),
    onSuccess: (data) => qc.setQueryData(["portfolio"], data),
  });
}

export function useDocuments(poll = false) {
  return useQuery({
    queryKey: ["documents"],
    queryFn: () => apiGet<{ documents: DocumentItem[] }>("/api/documents"),
    refetchInterval: poll ? 3000 : false,
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => apiUpload<DocumentItem>("/api/documents", file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiDelete(`/api/documents/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useAgents() {
  return useQuery({
    queryKey: ["agents"],
    queryFn: () => apiGet<{ agents: AgentInfo[] }>("/api/chat/agents"),
    staleTime: Infinity,
  });
}
