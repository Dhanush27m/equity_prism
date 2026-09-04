/**
 * Component: Frontend -> lib -> Formatting utilities
 * Belongs to: imported throughout components/pages wherever a number, date, or
 * conditional class needs consistent formatting.
 * Purpose: shared helpers for Tailwind class merging and Indian-market-specific number
 * formatting (₹ crores, INR locale grouping, percentage/sign display).
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// Merges conditional Tailwind class lists while resolving conflicting utility classes
// (e.g. a later `p-4` overriding an earlier `p-2`) — the standard clsx+tailwind-merge combo.
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Formats a raw rupee value into Indian crore notation (₹X Cr, or ₹X.XXL Cr for very
// large values) — the convention Indian financial UIs use instead of millions/billions.
export function formatCr(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const cr = value / 1e7;
  if (Math.abs(cr) >= 1e5) return `₹${(cr / 1e5).toFixed(2)}L Cr`;
  if (Math.abs(cr) >= 1) return `₹${cr.toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr`;
  return `₹${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

// Formats a price with ₹ and Indian locale grouping, always 2 decimal places.
export function formatPrice(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `₹${value.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Plain Indian-locale number formatting (no currency symbol).
export function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("en-IN", { maximumFractionDigits: digits });
}

// Formats a percentage, optionally converting a decimal (0.15 -> 15%) and optionally
// prefixing a "+" for positive values — matches the decimal-vs-percentage convention
// the backend's agent prompts also have to spell out for ratio fields.
export function formatPct(
  value: number | null | undefined,
  opts: { isDecimal?: boolean; digits?: number; sign?: boolean } = {}
): string {
  if (value == null || Number.isNaN(value)) return "—";
  const { isDecimal = false, digits = 2, sign = false } = opts;
  const pct = isDecimal ? value * 100 : value;
  const s = sign && pct > 0 ? "+" : "";
  return `${s}${pct.toFixed(digits)}%`;
}

// Formats an ISO date string as "12 Mar 2024" (falls back to the raw value if unparseable).
export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

// Formats a timestamp as "5m ago" / "3h ago" / "2d ago", falling back to a full date
// once it's more than 30 days old — used for news article timestamps.
export function formatRelativeTime(value: string | null | undefined): string {
  if (!value) return "";
  const d = new Date(value);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return formatDate(value);
}

// Returns the Tailwind text-color class matching a value's sign — used for P&L,
// change%, etc. throughout the UI.
export function signClass(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "text-muted-foreground";
  if (value > 0) return "text-positive";
  if (value < 0) return "text-negative";
  return "text-muted-foreground";
}
