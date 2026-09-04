/**
 * Component: Frontend -> app -> Company page (route "/company/[symbol]")
 * Belongs to: reached from search, the watchlist, or the screener — the deep-dive view
 * for a single stock.
 * Purpose: candlestick+volume price chart with period selection, key ratio tiles,
 * tabbed financial statements (income/balance/cashflow, annual/quarterly), rule-based
 * risk signals, and quick actions to watch the stock or jump into an AI analysis.
 */

"use client";

import { AlertTriangle, MessageSquare, Star } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import * as React from "react";

import { MetricCard, riskBadgeVariant } from "@/components/common";
import { PriceChart } from "@/components/price-chart";
import { EmptyState, ErrorState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useAddWatchlist,
  useCompany,
  useHistory,
  useRatios,
  useRisk,
  useStatement,
  useWatchlist,
} from "@/lib/hooks";
import type { RiskSignalItem } from "@/lib/types";
import { cn, formatCr, formatNumber, formatPct, formatPrice } from "@/lib/utils";

const PERIODS = ["1M", "3M", "6M", "1Y", "5Y"];

// The price chart card with its own period-selector state (always a live yfinance call
// per period — see api/routes/market.py's /history).
function ChartCard({ symbol }: { symbol: string }) {
  const [period, setPeriod] = React.useState("1Y");
  const { data, isLoading, isError, refetch } = useHistory(symbol, period);
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Price</CardTitle>
        <div className="flex gap-1">
          {PERIODS.map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={cn(
                "rounded px-2 py-1 text-xs font-medium",
                p === period ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
              )}
            >
              {p}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {isLoading ? (
          <Skeleton className="h-[380px] w-full" />
        ) : isError ? (
          <ErrorState message="No price history available." onRetry={refetch} />
        ) : (
          <PriceChart candles={data?.candles ?? []} />
        )}
      </CardContent>
    </Card>
  );
}

// The 6-tile key-ratio row (stored-first data — see api/routes/market.py's /ratios).
function MetricsRow({ symbol }: { symbol: string }) {
  const { data, isLoading } = useRatios(symbol);
  if (isLoading)
    return (
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      <MetricCard label="P/E" value={formatNumber(data?.pe)} />
      <MetricCard label="P/B" value={formatNumber(data?.pb)} />
      <MetricCard label="ROE" value={formatPct(data?.roe, { isDecimal: true })} />
      <MetricCard label="ROCE" value={formatPct(data?.roce, { isDecimal: true })} />
      <MetricCard label="D/E" value={data?.debt_to_equity != null ? formatNumber(data.debt_to_equity) : "—"} />
      <MetricCard label="Div Yield" value={formatPct(data?.dividend_yield)} />
    </div>
  );
}

// One financial-statement table (income/balance/cashflow) with its own annual/quarterly
// toggle; shows up to the first 14 line items, values formatted in ₹ crores.
function StatementTable({ symbol, kind }: { symbol: string; kind: string }) {
  const [pt, setPt] = React.useState("annual");
  const { data, isLoading } = useStatement(symbol, kind, pt);
  return (
    <div>
      <div className="mb-2 flex justify-end gap-1">
        {["annual", "quarterly"].map((p) => (
          <button
            key={p}
            onClick={() => setPt(p)}
            className={cn(
              "rounded px-2 py-1 text-xs capitalize",
              p === pt ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
            )}
          >
            {p}
          </button>
        ))}
      </div>
      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : !data?.periods.length ? (
        <EmptyState title="No statement data available" />
      ) : (
        <Table>
          <THead>
            <TR>
              <TH>Line item</TH>
              {data.periods.map((p) => (
                <TH key={p} className="text-right">
                  {p.slice(0, 7)}
                </TH>
              ))}
            </TR>
          </THead>
          <TBody>
            {Object.entries(data.rows)
              .slice(0, 14)
              .map(([label, values]) => (
                <TR key={label}>
                  <TD className="text-xs text-muted-foreground">{label}</TD>
                  {values.map((v, i) => (
                    <TD key={i} className="text-right tabular-nums text-xs">
                      {v == null ? "—" : formatCr(v)}
                    </TD>
                  ))}
                </TR>
              ))}
          </TBody>
        </Table>
      )}
    </div>
  );
}

// The rule-based risk-signals card (see services/ratios.py's compute_risk).
function RiskCard({ symbol }: { symbol: string }) {
  const { data, isLoading } = useRisk(symbol);
  const signals = (data?.signals as RiskSignalItem[]) ?? [];
  const badge = riskBadgeVariant(data?.score);
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" /> Risk signals
        </CardTitle>
        {!isLoading && <Badge variant={badge.variant}>{badge.label}</Badge>}
      </CardHeader>
      <CardContent className="pt-0">
        {isLoading ? (
          <Skeleton className="h-20 w-full" />
        ) : signals.length === 0 ? (
          <div className="text-sm text-muted-foreground">No risk flags detected.</div>
        ) : (
          <ul className="space-y-2">
            {signals.map((s, i) => (
              <li key={i} className="flex items-center gap-2 text-sm">
                <span
                  className={cn(
                    "h-2 w-2 rounded-full",
                    (s.severity ?? 1) >= 2 ? "bg-negative" : "bg-[var(--warning)]"
                  )}
                />
                {s.label ?? s.code}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export default function CompanyPage() {
  const params = useParams();
  const symbol = String(params.symbol ?? "").toUpperCase();
  const { data: company, isLoading, isError, refetch } = useCompany(symbol);
  const { data: watchlist } = useWatchlist();
  const addWatch = useAddWatchlist();

  const inWatchlist = watchlist?.items.some((w) => w.symbol === symbol);

  if (isError)
    return <ErrorState message={`Could not load ${symbol}.`} onRetry={refetch} />;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          {isLoading ? (
            <Skeleton className="h-8 w-48" />
          ) : (
            <>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-semibold">{symbol}</h1>
                <Badge variant="outline">{company?.exchange}</Badge>
                {company?.sector && <Badge variant="neutral">{company.sector}</Badge>}
              </div>
              <div className="mt-0.5 text-sm text-muted-foreground">{company?.name}</div>
            </>
          )}
        </div>
        <div className="flex items-center gap-3">
          {company?.current_price != null && (
            <div className="text-right">
              <div className="text-2xl font-semibold tabular-nums">
                {formatPrice(company.current_price)}
              </div>
              <div className="text-xs text-muted-foreground">{formatCr(company.market_cap)} mkt cap</div>
            </div>
          )}
          <Button
            variant={inWatchlist ? "secondary" : "outline"}
            size="sm"
            onClick={() => addWatch.mutate(symbol)}
            disabled={inWatchlist || addWatch.isPending}
          >
            <Star className={cn("h-4 w-4", inWatchlist && "fill-current")} />
            {inWatchlist ? "Watching" : "Watch"}
          </Button>
          <Link href={`/chat?q=${encodeURIComponent(`Analyze ${symbol} as an investment`)}`}>
            <Button size="sm">
              <MessageSquare className="h-4 w-4" /> Ask AI
            </Button>
          </Link>
        </div>
      </div>

      <ChartCard symbol={symbol} />
      <MetricsRow symbol={symbol} />

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Financial statements</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <Tabs defaultValue="income">
              <TabsList>
                <TabsTrigger value="income">Income</TabsTrigger>
                <TabsTrigger value="balance">Balance</TabsTrigger>
                <TabsTrigger value="cashflow">Cash flow</TabsTrigger>
              </TabsList>
              <TabsContent value="income">
                <StatementTable symbol={symbol} kind="income" />
              </TabsContent>
              <TabsContent value="balance">
                <StatementTable symbol={symbol} kind="balance" />
              </TabsContent>
              <TabsContent value="cashflow">
                <StatementTable symbol={symbol} kind="cashflow" />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
        <RiskCard symbol={symbol} />
      </div>
    </div>
  );
}
