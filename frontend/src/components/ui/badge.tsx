/**
 * Component: Frontend -> components/ui -> Badge primitive
 * Belongs to: the base UI kit (src/components/ui) reused across risk/sentiment/citation
 * chips throughout the app.
 * Purpose: a small colored pill for status labels (risk level, sentiment, citation type).
 */

import * as React from "react";

import { cn } from "@/lib/utils";

type Variant = "default" | "positive" | "negative" | "neutral" | "warning" | "outline";

const variants: Record<Variant, string> = {
  default: "bg-primary/10 text-primary",
  positive: "bg-positive-bg text-positive",
  negative: "bg-negative-bg text-negative",
  neutral: "bg-neutral-bg text-neutral",
  warning: "bg-[var(--warning)]/15 text-[var(--warning)]",
  outline: "border border-border text-muted-foreground",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
