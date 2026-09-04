/**
 * Component: Frontend -> components -> Generic page-state placeholders
 * Belongs to: reused by every page for its loading/error/empty states, and as each
 * page's title/subtitle/action-button header.
 * Purpose: consistent, reusable UI for the three states every data-driven page has to
 * handle — an error card (with optional retry), an empty-results card, and a standard
 * page title/subtitle/action row.
 */

"use client";

import { AlertCircle, Inbox } from "lucide-react";

import { Button } from "@/components/ui/button";

// Shown when a query fails — an alert icon, message, and optional retry button.
export function ErrorState({
  message,
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed p-8 text-center">
      <AlertCircle className="h-8 w-8 text-negative" />
      <div className="text-sm text-muted-foreground">{message ?? "Something went wrong."}</div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

// Shown when a query succeeds but returns no results.
export function EmptyState({
  title,
  hint,
  icon,
}: {
  title: string;
  hint?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-8 text-center">
      <div className="text-muted-foreground">{icon ?? <Inbox className="h-8 w-8" />}</div>
      <div className="text-sm font-medium">{title}</div>
      {hint && <div className="text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}

// The standard title/subtitle/action row every page opens with.
export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-5 flex items-end justify-between gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-0.5 text-sm text-muted-foreground">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
