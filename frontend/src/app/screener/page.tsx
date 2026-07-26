"use client";

import { ArrowDown, ArrowUp, Filter, Star } from "lucide-react";
import { useRouter } from "next/navigation";
import * as React from "react";

import { EmptyState, ErrorState } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useAddWatchlist, useCompanies, useScreener, type ScreenerFilters } from "@/lib/hooks";
import { cn, formatCr, formatNumber, formatPct, formatPrice } from "@/lib/utils";

interface FormState {
  sector: string;
  market_cap_min_cr: string;
  pe_min: string;
  pe_max: string;
  roe_min_pct: string;
  dividend_yield_min_pct: string;
}

const EMPTY: FormState = {
  sector: "",
  market_cap_min_cr: "",
  pe_min: "",
  pe_max: "",
  roe_min_pct: "",
  dividend_yield_min_pct: "",
};

function num(v: string): number | undefined {
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : undefined;
}

export default function ScreenerPage() {
  const router = useRouter();
  const addWatch = useAddWatchlist();
  const { data: companies } = useCompanies({});
  const sectors = React.useMemo(
    () => Array.from(new Set((companies ?? []).map((c) => c.sector).filter(Boolean))).sort() as string[],
    [companies]
  );

  const [form, setForm] = React.useState<FormState>(EMPTY);
  const [applied, setApplied] = React.useState<FormState>(EMPTY);
  const [sort, setSort] = React.useState<{ by: string; desc: boolean }>({ by: "market_cap", desc: true });

  const filters: ScreenerFilters = {
    sector: applied.sector || undefined,
    market_cap_min: num(applied.market_cap_min_cr) != null ? num(applied.market_cap_min_cr)! * 1e7 : undefined,
    pe_min: num(applied.pe_min),
    pe_max: num(applied.pe_max),
    roe_min: num(applied.roe_min_pct) != null ? num(applied.roe_min_pct)! / 100 : undefined,
    dividend_yield_min: num(applied.dividend_yield_min_pct),
    sort_by: sort.by,
    desc: sort.desc,
  };

  const { data, isLoading, isError, refetch } = useScreener(filters);

  function toggleSort(col: string) {
    setSort((s) => (s.by === col ? { by: col, desc: !s.desc } : { by: col, desc: true }));
  }

  const set = (k: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const cols: { key: string; label: string; sortable: boolean }[] = [
    { key: "symbol", label: "Stock", sortable: true },
    { key: "market_cap", label: "Mkt Cap", sortable: true },
    { key: "current_price", label: "Price", sortable: false },
    { key: "pe", label: "P/E", sortable: true },
    { key: "roe", label: "ROE", sortable: true },
    { key: "dividend_yield", label: "Div Yield", sortable: true },
  ];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Screener</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">Filter Nifty 50 stocks by fundamentals</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-4 w-4" /> Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Sector</label>
              <Select value={form.sector} onChange={set("sector")}>
                <option value="">All</option>
                {sectors.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Min Mkt Cap (Cr)</label>
              <input value={form.market_cap_min_cr} onChange={set("market_cap_min_cr")} type="number" className="h-9 w-full rounded-md border border-input bg-card px-3 text-sm" />
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">P/E min</label>
              <input value={form.pe_min} onChange={set("pe_min")} type="number" className="h-9 w-full rounded-md border border-input bg-card px-3 text-sm" />
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">P/E max</label>
              <input value={form.pe_max} onChange={set("pe_max")} type="number" className="h-9 w-full rounded-md border border-input bg-card px-3 text-sm" />
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">ROE min (%)</label>
              <input value={form.roe_min_pct} onChange={set("roe_min_pct")} type="number" className="h-9 w-full rounded-md border border-input bg-card px-3 text-sm" />
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Div Yield min (%)</label>
              <input value={form.dividend_yield_min_pct} onChange={set("dividend_yield_min_pct")} type="number" className="h-9 w-full rounded-md border border-input bg-card px-3 text-sm" />
            </div>
          </div>
          <div className="mt-3 flex gap-2">
            <Button size="sm" onClick={() => setApplied(form)}>
              Apply filters
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setForm(EMPTY);
                setApplied(EMPTY);
              }}
            >
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{data ? `${data.count} results` : "Results"}</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : isError ? (
            <ErrorState onRetry={refetch} />
          ) : !data?.results.length ? (
            <EmptyState title="No stocks match these filters" hint="Try widening the ranges." />
          ) : (
            <Table>
              <THead>
                <TR>
                  {cols.map((c) => (
                    <TH
                      key={c.key}
                      className={cn(c.key !== "symbol" && "text-right", c.sortable && "cursor-pointer select-none")}
                      onClick={() => c.sortable && toggleSort(c.key)}
                    >
                      <span className={cn("inline-flex items-center gap-1", c.key !== "symbol" && "justify-end")}>
                        {c.label}
                        {sort.by === c.key &&
                          (sort.desc ? <ArrowDown className="h-3 w-3" /> : <ArrowUp className="h-3 w-3" />)}
                      </span>
                    </TH>
                  ))}
                  <TH></TH>
                </TR>
              </THead>
              <TBody>
                {data.results.map((r) => (
                  <TR
                    key={r.symbol}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => router.push(`/company/${r.symbol}`)}
                  >
                    <TD>
                      <div className="font-medium">{r.symbol}</div>
                      <div className="text-xs text-muted-foreground">{r.sector}</div>
                    </TD>
                    <TD className="text-right tabular-nums">{formatCr(r.market_cap)}</TD>
                    <TD className="text-right tabular-nums">{formatPrice(r.current_price)}</TD>
                    <TD className="text-right tabular-nums">{formatNumber(r.pe)}</TD>
                    <TD className="text-right tabular-nums">{formatPct(r.roe, { isDecimal: true })}</TD>
                    <TD className="text-right tabular-nums">{formatPct(r.dividend_yield)}</TD>
                    <TD className="text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          addWatch.mutate(r.symbol);
                        }}
                        className="text-muted-foreground hover:text-primary"
                        title="Add to watchlist"
                      >
                        <Star className="h-4 w-4" />
                      </button>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
