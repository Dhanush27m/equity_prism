"use client";

import { ArrowRight, Sparkles, Star, TrendingUp } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";

import { Delta, riskBadgeVariant } from "@/components/common";
import { EmptyState, ErrorState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useIndices, usePortfolio, useWatchlist } from "@/lib/hooks";
import { cn, formatCr, formatPct, formatPrice, signClass } from "@/lib/utils";

const ALLOC_COLORS = [
  "bg-blue-500",
  "bg-emerald-500",
  "bg-amber-500",
  "bg-violet-500",
  "bg-rose-500",
  "bg-cyan-500",
  "bg-lime-500",
];

function IndexCard({
  name,
  value,
  change,
  pct,
}: {
  name: string;
  value: number | null;
  change: number | null;
  pct: number | null;
}) {
  return (
    <Card className="p-4">
      <div className="text-xs font-medium text-muted-foreground">{name}</div>
      <div className="mt-1.5 text-xl font-semibold tabular-nums">
        {value != null ? value.toLocaleString("en-IN") : "—"}
      </div>
      <div className={cn("mt-0.5 text-sm tabular-nums", signClass(pct))}>
        {change != null ? `${change > 0 ? "+" : ""}${change.toFixed(2)}` : "—"}{" "}
        {pct != null && <span>({formatPct(pct, { sign: true })})</span>}
      </div>
    </Card>
  );
}

function QuickAsk() {
  const router = useRouter();
  const [q, setQ] = React.useState("");
  return (
    <Card className="bg-gradient-to-br from-primary/10 to-transparent">
      <CardContent className="p-4">
        <div className="mb-2 flex items-center gap-2 text-sm font-medium">
          <Sparkles className="h-4 w-4 text-primary" />
          Ask Prism
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (q.trim()) router.push(`/chat?q=${encodeURIComponent(q.trim())}`);
          }}
          className="flex gap-2"
        >
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="e.g. Compare TCS and Infosys, or analyze Reliance…"
            className="h-9 flex-1 rounded-md border border-input bg-card px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <Button type="submit" size="sm">
            Ask <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function Watchlist() {
  const { data, isLoading, isError, refetch } = useWatchlist();
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Star className="h-4 w-4" /> Watchlist
        </CardTitle>
        <Link href="/screener" className="text-xs text-primary hover:underline">
          Add via screener
        </Link>
      </CardHeader>
      <CardContent className="pt-0">
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        ) : isError ? (
          <ErrorState onRetry={refetch} />
        ) : !data?.items.length ? (
          <EmptyState
            title="No stocks in your watchlist"
            hint="Add stocks from the screener or a company page."
            icon={<Star className="h-8 w-8" />}
          />
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Symbol</TH>
                <TH className="text-right">Price</TH>
                <TH className="text-right">Mkt Cap</TH>
                <TH className="text-right">Risk</TH>
              </TR>
            </THead>
            <TBody>
              {data.items.map((it) => {
                const risk = riskBadgeVariant(it.risk_score);
                return (
                  <TR key={it.id} className="hover:bg-muted/50">
                    <TD>
                      <Link href={`/company/${it.symbol}`} className="font-medium hover:text-primary">
                        {it.symbol}
                      </Link>
                      <div className="text-xs text-muted-foreground">{it.name}</div>
                    </TD>
                    <TD className="text-right tabular-nums">{formatPrice(it.current_price)}</TD>
                    <TD className="text-right tabular-nums text-muted-foreground">
                      {formatCr(it.market_cap)}
                    </TD>
                    <TD className="text-right">
                      <Badge variant={risk.variant}>{risk.label}</Badge>
                    </TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function PortfolioSummary() {
  const { data, isLoading } = usePortfolio();
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4" /> Portfolio
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        {isLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : (
          <>
            <div>
              <div className="text-xs text-muted-foreground">Current value</div>
              <div className="text-2xl font-semibold tabular-nums">
                {formatPrice(data?.summary.current_value ?? 0)}
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Total P&L</span>
              <Delta pct={data?.summary.pl_pct} />
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Invested</span>
              <span className="tabular-nums">{formatPrice(data?.summary.invested ?? 0)}</span>
            </div>
            {data?.sector_allocation.length ? (
              <div>
                <div className="mb-1.5 text-xs text-muted-foreground">Sector allocation</div>
                <div className="flex h-2.5 overflow-hidden rounded-full">
                  {data.sector_allocation.map((s, i) => (
                    <div
                      key={s.sector}
                      style={{ width: `${s.pct}%` }}
                      className={cn("h-full", ALLOC_COLORS[i % ALLOC_COLORS.length])}
                      title={`${s.sector} ${s.pct}%`}
                    />
                  ))}
                </div>
              </div>
            ) : null}
            <Link href="/portfolio">
              <Button variant="outline" size="sm" className="w-full">
                Manage portfolio
              </Button>
            </Link>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data: indices, isLoading, isError, refetch } = useIndices();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Indian market overview & your positions
        </p>
      </div>

      {isError ? (
        <ErrorState message="Could not load market indices." onRetry={refetch} />
      ) : (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {isLoading
            ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24 w-full" />)
            : indices?.indices.map((idx) => (
                <IndexCard
                  key={idx.key}
                  name={idx.name}
                  value={idx.value}
                  change={idx.change}
                  pct={idx.change_pct}
                />
              ))}
        </div>
      )}

      <QuickAsk />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Watchlist />
        </div>
        <PortfolioSummary />
      </div>
    </div>
  );
}
