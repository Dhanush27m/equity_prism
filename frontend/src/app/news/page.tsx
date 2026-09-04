/**
 * Component: Frontend -> app -> News page (route "/news")
 * Belongs to: the News & Sentiment screen.
 * Purpose: shows recent headlines for a chosen symbol (GET /api/news/{symbol}) with a
 * quick sentiment gauge. Note: the sentiment classification here is a simple client-side
 * keyword match (POSITIVE/NEGATIVE word lists below) — a fast, free, local heuristic for
 * the gauge, entirely separate from the backend's LLM-based sentiment specialist agent,
 * which the "Deep sentiment via AI" button links out to for a real analysis.
 */

"use client";

import { ExternalLink, Newspaper, Sparkles } from "lucide-react";
import Link from "next/link";
import * as React from "react";

import { EmptyState, ErrorState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useCompanies, useNews } from "@/lib/hooks";
import { cn, formatRelativeTime } from "@/lib/utils";

const POSITIVE = [
  "surge", "gain", "profit", "rise", "rises", "jump", "beat", "beats", "record", "high",
  "growth", "grows", "upgrade", "buy", "bullish", "outperform", "strong", "wins", "win",
  "deal", "expansion", "rally", "soar", "boost", "positive", "approval", "dividend",
];
const NEGATIVE = [
  "fall", "falls", "drop", "drops", "loss", "losses", "decline", "cut", "cuts", "downgrade",
  "sell", "bearish", "weak", "miss", "misses", "slump", "plunge", "fraud", "probe", "fine",
  "penalty", "concern", "risk", "warning", "slowdown", "low", "crash", "lawsuit", "resign",
];

type Sentiment = "bullish" | "bearish" | "neutral";

// Client-side keyword-count classifier for one headline — purely local, no API call.
function classify(title: string): Sentiment {
  const t = title.toLowerCase();
  let score = 0;
  for (const w of POSITIVE) if (t.includes(w)) score += 1;
  for (const w of NEGATIVE) if (t.includes(w)) score -= 1;
  if (score > 0) return "bullish";
  if (score < 0) return "bearish";
  return "neutral";
}

// A horizontal bearish<->bullish gauge with a marker positioned by net sentiment ratio
// across the currently-loaded headlines.
function Gauge({ bullish, bearish, neutral }: { bullish: number; bearish: number; neutral: number }) {
  const total = bullish + bearish + neutral || 1;
  const net = (bullish - bearish) / total;
  const pct = ((net + 1) / 2) * 100;
  const label = net > 0.15 ? "Bullish" : net < -0.15 ? "Bearish" : "Neutral";
  const color = net > 0.15 ? "text-positive" : net < -0.15 ? "text-negative" : "text-neutral";
  return (
    <div className="space-y-3">
      <div className="text-center">
        <div className={cn("text-2xl font-semibold", color)}>{label}</div>
        <div className="text-xs text-muted-foreground">Based on {total} recent headlines</div>
      </div>
      <div className="relative h-2.5 rounded-full bg-gradient-to-r from-negative via-neutral to-positive">
        <div
          className="absolute top-1/2 h-4 w-1 -translate-y-1/2 rounded-full bg-foreground shadow"
          style={{ left: `calc(${pct}% - 2px)` }}
        />
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Bearish {bearish}</span>
        <span>Neutral {neutral}</span>
        <span>Bullish {bullish}</span>
      </div>
    </div>
  );
}

export default function NewsPage() {
  const { data: companies } = useCompanies({});
  const [symbol, setSymbol] = React.useState("RELIANCE");
  const [q, setQ] = React.useState("");
  const { data, isLoading, isError, refetch } = useNews(symbol);

  const options = (q ? companies ?? [] : []).filter(
    (c) => c.symbol.toLowerCase().includes(q.toLowerCase()) || c.name.toLowerCase().includes(q.toLowerCase())
  ).slice(0, 6);

  const articles = (data?.articles ?? []).map((a) => ({ ...a, sentiment: classify(a.title) }));
  const counts = articles.reduce(
    (acc, a) => {
      acc[a.sentiment] += 1;
      return acc;
    },
    { bullish: 0, bearish: 0, neutral: 0 } as Record<Sentiment, number>
  );

  const badgeVariant = (s: Sentiment) =>
    s === "bullish" ? "positive" : s === "bearish" ? "negative" : "neutral";

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">News & Sentiment</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">Latest headlines with a sentiment read</p>
        </div>
        <div className="relative w-56">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={`Filter by stock (${symbol})`}
            className="h-9 w-full rounded-md border border-input bg-card px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          {q && options.length > 0 && (
            <div className="absolute z-30 mt-1 w-full overflow-hidden rounded-md border border-border bg-card shadow-lg">
              {options.map((c) => (
                <button
                  key={c.symbol}
                  onClick={() => {
                    setSymbol(c.symbol);
                    setQ("");
                  }}
                  className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-muted"
                >
                  <span className="font-medium">{c.symbol}</span>
                  <span className="text-xs text-muted-foreground">{c.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>{symbol} sentiment</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {isLoading ? (
              <Skeleton className="h-24 w-full" />
            ) : (
              <>
                <Gauge {...counts} />
                <Link href={`/chat?q=${encodeURIComponent(`What is the latest news sentiment on ${symbol}?`)}`}>
                  <Button variant="outline" size="sm" className="mt-4 w-full">
                    <Sparkles className="h-4 w-4" /> Deep sentiment via AI
                  </Button>
                </Link>
              </>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Headlines</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-14 w-full" />
                ))}
              </div>
            ) : isError ? (
              <ErrorState onRetry={refetch} />
            ) : !articles.length ? (
              <EmptyState title="No recent news" icon={<Newspaper className="h-8 w-8" />} />
            ) : (
              <div className="divide-y divide-border">
                {articles.map((a, i) => (
                  <a
                    key={i}
                    href={a.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-start gap-3 py-3 first:pt-0 hover:opacity-80"
                  >
                    <Badge variant={badgeVariant(a.sentiment)} className="mt-0.5 shrink-0 capitalize">
                      {a.sentiment}
                    </Badge>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium">{a.title}</div>
                      <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                        {a.source && <span>{a.source}</span>}
                        {a.published && <span>· {formatRelativeTime(a.published)}</span>}
                      </div>
                    </div>
                    <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                  </a>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
