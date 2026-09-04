/**
 * Component: Frontend -> app -> Compare page (route "/compare")
 * Belongs to: side-by-side stock comparison, backed by the comparator specialist agent
 * for the AI verdict.
 * Purpose: pick 2-5 stocks, see per-metric bar charts and a full metrics table (all from
 * GET /api/companies/{symbol}/ratios via useMultiRatios — one query per symbol run in
 * parallel), then optionally stream an AI-written relative verdict from the backend.
 */

"use client";

import { GitCompareArrows, Sparkles, X } from "lucide-react";
import * as React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Citations } from "@/components/citations";
import { Markdown } from "@/components/markdown";
import { EmptyState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { streamChat, type SSEEvent } from "@/lib/api";
import { useCompanies, useMultiRatios } from "@/lib/hooks";
import type { Citation } from "@/lib/types";
import { cn, formatNumber, formatPct } from "@/lib/utils";

const BAR_COLORS = ["#2563eb", "#16a34a", "#d97706", "#7c3aed", "#dc2626"];

// Search-and-add stock picker, capped at 5 selections.
function Picker({
  selected,
  onToggle,
}: {
  selected: string[];
  onToggle: (s: string) => void;
}) {
  const [q, setQ] = React.useState("");
  const { data } = useCompanies(q ? { search: q } : {});
  const options = (q ? data ?? [] : []).slice(0, 6);
  return (
    <div className="relative">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search and add up to 5 stocks…"
        className="h-9 w-full rounded-md border border-input bg-card px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
      {q && options.length > 0 && (
        <div className="absolute z-30 mt-1 w-full overflow-hidden rounded-md border border-border bg-card shadow-lg">
          {options.map((c) => (
            <button
              key={c.symbol}
              onClick={() => {
                onToggle(c.symbol);
                setQ("");
              }}
              disabled={selected.includes(c.symbol) || selected.length >= 5}
              className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-muted disabled:opacity-40"
            >
              <span className="font-medium">{c.symbol}</span>
              <span className="text-xs text-muted-foreground">{c.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// One metric's bar chart across the selected stocks (isDecimal converts 0.15 -> 15,
// matching the backend's ratio-field convention).
function MetricBar({
  title,
  data,
  isDecimal,
}: {
  title: string;
  data: { symbol: string; value: number | null }[];
  isDecimal?: boolean;
}) {
  const chartData = data.map((d) => ({
    symbol: d.symbol,
    value: d.value == null ? 0 : isDecimal ? d.value * 100 : d.value,
  }));
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xs">{title}</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="symbol" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
            <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
            <Tooltip
              contentStyle={{
                background: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export default function ComparePage() {
  const [selected, setSelected] = React.useState<string[]>([]);
  const [answer, setAnswer] = React.useState("");
  const [citations, setCitations] = React.useState<Citation[]>([]);
  const [busy, setBusy] = React.useState(false);

  const results = useMultiRatios(selected);
  const loadingRatios = results.some((r) => r.isLoading);

  function toggle(s: string) {
    setSelected((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));
  }

  const rows = selected.map((s, i) => ({ symbol: s, ratios: results[i]?.data }));

  // Sends a comparison question straight to the backend (bypassing the chat thread
  // store, like Documents/Portfolio's inline AI boxes) — the router will select the
  // comparator agent since 2+ symbols are present in the question text.
  async function compare() {
    if (selected.length < 2 || busy) return;
    setBusy(true);
    setAnswer("");
    setCitations([]);
    let content = "";
    const q = `Compare ${selected.join(", ")} on valuation, profitability, leverage and growth.`;
    try {
      await streamChat(q, null, (ev: SSEEvent) => {
        if (ev.type === "token") {
          content += (ev.content as string) ?? "";
          setAnswer(content);
        } else if (ev.type === "done") {
          setCitations((ev.citations as Citation[]) ?? []);
        }
      });
    } catch {
      setAnswer("Comparison failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  const metricDefs: { title: string; key: keyof NonNullable<(typeof rows)[0]["ratios"]>; isDecimal?: boolean }[] = [
    { title: "P/E ratio", key: "pe" },
    { title: "ROE (%)", key: "roe", isDecimal: true },
    { title: "Debt / Equity", key: "debt_to_equity" },
    { title: "Net margin (%)", key: "net_margin", isDecimal: true },
  ];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Compare</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Pick 2–5 stocks to compare metrics side by side and get an AI verdict.
        </p>
      </div>

      <Card>
        <CardContent className="space-y-3 p-4">
          <Picker selected={selected} onToggle={toggle} />
          <div className="flex flex-wrap items-center gap-2">
            {selected.map((s) => (
              <Badge key={s} variant="default" className="gap-1 py-1">
                {s}
                <button onClick={() => toggle(s)}>
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
            {selected.length >= 2 && (
              <Button size="sm" className="ml-auto" onClick={compare} disabled={busy}>
                <Sparkles className="h-4 w-4" /> {busy ? "Comparing…" : "Ask Prism to compare"}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {selected.length < 2 ? (
        <EmptyState
          title="Add at least 2 stocks"
          hint="Search above to build a comparison."
          icon={<GitCompareArrows className="h-8 w-8" />}
        />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {metricDefs.map((m) => (
              <MetricBar
                key={m.key}
                title={m.title}
                isDecimal={m.isDecimal}
                data={rows.map((r) => ({
                  symbol: r.symbol,
                  value: (r.ratios?.[m.key] as number | null) ?? null,
                }))}
              />
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Metrics table</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {loadingRatios ? (
                <Skeleton className="h-40 w-full" />
              ) : (
                <Table>
                  <THead>
                    <TR>
                      <TH>Metric</TH>
                      {rows.map((r) => (
                        <TH key={r.symbol} className="text-right">
                          {r.symbol}
                        </TH>
                      ))}
                    </TR>
                  </THead>
                  <TBody>
                    {(
                      [
                        ["P/E", "pe", false],
                        ["P/B", "pb", false],
                        ["ROE", "roe", true],
                        ["ROCE", "roce", true],
                        ["Debt/Equity", "debt_to_equity", false],
                        ["Net margin", "net_margin", true],
                        ["Div yield", "dividend_yield", false],
                        ["Rev growth", "revenue_growth", true],
                      ] as [string, keyof NonNullable<(typeof rows)[0]["ratios"]>, boolean][]
                    ).map(([label, key, dec]) => (
                      <TR key={label}>
                        <TD className="text-muted-foreground">{label}</TD>
                        {rows.map((r) => {
                          const v = r.ratios?.[key] as number | null | undefined;
                          return (
                            <TD key={r.symbol} className="text-right tabular-nums">
                              {v == null ? "—" : dec ? formatPct(v, { isDecimal: true }) : formatNumber(v)}
                            </TD>
                          );
                        })}
                      </TR>
                    ))}
                  </TBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {(answer || busy) && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" /> AI verdict
                </CardTitle>
              </CardHeader>
              <CardContent className={cn("pt-0")}>
                {answer ? (
                  <Markdown>{answer}</Markdown>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-primary" /> Analyzing…
                  </div>
                )}
                {citations.length > 0 && <Citations citations={citations} />}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
