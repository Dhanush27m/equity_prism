import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCr(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const cr = value / 1e7;
  if (Math.abs(cr) >= 1e5) return `₹${(cr / 1e5).toFixed(2)}L Cr`;
  if (Math.abs(cr) >= 1) return `₹${cr.toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr`;
  return `₹${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export function formatPrice(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `₹${value.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("en-IN", { maximumFractionDigits: digits });
}

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

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

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

export function signClass(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "text-muted-foreground";
  if (value > 0) return "text-positive";
  if (value < 0) return "text-negative";
  return "text-muted-foreground";
}
