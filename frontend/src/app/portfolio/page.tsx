"use client";

import { Briefcase, Plus, Sparkles, Trash2 } from "lucide-react";
import * as React from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { Citations } from "@/components/citations";
import { Delta, MetricCard } from "@/components/common";
import { Markdown } from "@/components/markdown";
import { EmptyState } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { streamChat, type SSEEvent } from "@/lib/api";
import { useAddHolding, usePortfolio, useRemoveHolding } from "@/lib/hooks";
import type { Citation } from "@/lib/types";
import { formatPct, formatPrice, signClass } from "@/lib/utils";

const COLORS = ["#2563eb", "#16a34a", "#d97706", "#7c3aed", "#dc2626", "#0891b2", "#65a30d"];

function AddForm() {
  const add = useAddHolding();
  const [symbol, setSymbol] = React.useState("");
  const [qty, setQty] = React.useState("");
  const [price, setPrice] = React.useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const q = parseFloat(qty);
    const p = parseFloat(price);
    if (!symbol.trim() || !(q > 0) || !(p > 0)) return;
    add.mutate(
      { symbol: symbol.trim().toUpperCase(), quantity: q, avg_price: p },
      {
        onSuccess: () => {
          setSymbol("");
          setQty("");
          setPrice("");
        },
      }
    );
  }

  return (
    <form onSubmit={submit} className="flex flex-wrap items-end gap-2">
      <div className="flex-1 min-w-[120px]">
        <label className="mb-1 block text-xs text-muted-foreground">Symbol</label>
        <input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="RELIANCE"
          className="h-9 w-full rounded-md border border-input bg-card px-3 text-sm uppercase focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>
      <div className="w-24">
        <label className="mb-1 block text-xs text-muted-foreground">Qty</label>
        <input
          value={qty}
          onChange={(e) => setQty(e.target.value)}
          type="number"
          min="0"
          className="h-9 w-full rounded-md border border-input bg-card px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>
      <div className="w-28">
        <label className="mb-1 block text-xs text-muted-foreground">Avg price</label>
        <input
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          type="number"
          min="0"
          step="0.01"
          className="h-9 w-full rounded-md border border-input bg-card px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>
      <Button type="submit" size="md" disabled={add.isPending}>
        <Plus className="h-4 w-4" /> Add
      </Button>
    </form>
  );
}

export default function PortfolioPage() {
  const { data, isLoading } = usePortfolio();
  const remove = useRemoveHolding();
  const [answer, setAnswer] = React.useState("");
  const [citations, setCitations] = React.useState<Citation[]>([]);
  const [busy, setBusy] = React.useState(false);

  async function analyze() {
    if (busy) return;
    setBusy(true);
    setAnswer("");
    setCitations([]);
    let content = "";
    try {
      await streamChat(
        "Review my portfolio: overall P&L, biggest winners and losers, and concentration risk.",
        null,
        (ev: SSEEvent) => {
          if (ev.type === "token") {
            content += (ev.content as string) ?? "";
            setAnswer(content);
          } else if (ev.type === "done") {
            setCitations((ev.citations as Citation[]) ?? []);
          }
        }
      );
    } catch {
      setAnswer("Analysis failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  const summary = data?.summary;
  const holdings = data?.holdings ?? [];

  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Portfolio</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">Track holdings with live P&L</p>
        </div>
        {holdings.length > 0 && (
          <Button size="sm" onClick={analyze} disabled={busy}>
            <Sparkles className="h-4 w-4" /> {busy ? "Analyzing…" : "Analyze Portfolio"}
          </Button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <MetricCard label="Current value" value={isLoading ? "…" : formatPrice(summary?.current_value ?? 0)} />
        <MetricCard label="Invested" value={isLoading ? "…" : formatPrice(summary?.invested ?? 0)} />
        <MetricCard
          label="Total P&L"
          value={<span className={signClass(summary?.pl)}>{formatPrice(summary?.pl ?? 0)}</span>}
        />
        <MetricCard label="Return" value={<Delta pct={summary?.pl_pct} />} />
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Holdings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pt-0">
            <AddForm />
            {isLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : holdings.length === 0 ? (
              <EmptyState
                title="No holdings yet"
                hint="Add your first position above."
                icon={<Briefcase className="h-8 w-8" />}
              />
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Stock</TH>
                    <TH className="text-right">Qty</TH>
                    <TH className="text-right">Avg</TH>
                    <TH className="text-right">LTP</TH>
                    <TH className="text-right">Value</TH>
                    <TH className="text-right">P&L</TH>
                    <TH></TH>
                  </TR>
                </THead>
                <TBody>
                  {holdings.map((h) => (
                    <TR key={h.id}>
                      <TD>
                        <div className="font-medium">{h.symbol}</div>
                        <div className="text-xs text-muted-foreground">{h.sector}</div>
                      </TD>
                      <TD className="text-right tabular-nums">{h.quantity}</TD>
                      <TD className="text-right tabular-nums">{formatPrice(h.avg_price)}</TD>
                      <TD className="text-right tabular-nums">{formatPrice(h.current_price)}</TD>
                      <TD className="text-right tabular-nums">{formatPrice(h.current_value)}</TD>
                      <TD className="text-right">
                        <div className={signClass(h.pl)}>{formatPrice(h.pl)}</div>
                        <div className="text-xs">
                          <Delta pct={h.pl_pct} />
                        </div>
                      </TD>
                      <TD className="text-right">
                        <button
                          onClick={() => remove.mutate(h.id)}
                          className="text-muted-foreground hover:text-negative"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sector allocation</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {!data?.sector_allocation.length ? (
              <div className="py-8 text-center text-sm text-muted-foreground">No data</div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={data.sector_allocation}
                      dataKey="value"
                      nameKey="sector"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={2}
                    >
                      {data.sector_allocation.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: "var(--card)",
                        border: "1px solid var(--border)",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-1">
                  {data.sector_allocation.map((s, i) => (
                    <div key={s.sector} className="flex items-center gap-2 text-xs">
                      <span
                        className="h-2.5 w-2.5 rounded-sm"
                        style={{ background: COLORS[i % COLORS.length] }}
                      />
                      <span className="flex-1 truncate">{s.sector}</span>
                      <span className="tabular-nums text-muted-foreground">{formatPct(s.pct)}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {(answer || busy) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" /> Portfolio analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
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
    </div>
  );
}
