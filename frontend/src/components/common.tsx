"use client";

import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn, formatPct, signClass } from "@/lib/utils";

export function Delta({
  value,
  pct,
  isDecimal = false,
  className,
}: {
  value?: number | null;
  pct?: number | null;
  isDecimal?: boolean;
  className?: string;
}) {
  const ref = pct ?? value ?? null;
  if (ref == null) return <span className="text-muted-foreground">—</span>;
  const up = ref > 0;
  const down = ref < 0;
  return (
    <span className={cn("inline-flex items-center gap-0.5 font-medium", signClass(ref), className)}>
      {up && <ArrowUpRight className="h-3.5 w-3.5" />}
      {down && <ArrowDownRight className="h-3.5 w-3.5" />}
      {pct != null ? formatPct(pct, { isDecimal, sign: true }) : value}
    </span>
  );
}

export function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
}) {
  return (
    <Card className="p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold tabular-nums">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-muted-foreground">{hint}</div>}
    </Card>
  );
}

export function riskBadgeVariant(score: number | null | undefined) {
  if (score == null) return { variant: "neutral" as const, label: "No data" };
  if (score >= 5) return { variant: "negative" as const, label: "High risk" };
  if (score >= 2) return { variant: "warning" as const, label: "Moderate" };
  return { variant: "positive" as const, label: "Low risk" };
}

export function sentimentVariant(label: string | null | undefined) {
  const l = (label ?? "").toLowerCase();
  if (l.includes("bull") || l.includes("positive")) return "positive" as const;
  if (l.includes("bear") || l.includes("negative")) return "negative" as const;
  return "neutral" as const;
}
