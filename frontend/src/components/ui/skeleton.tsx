/**
 * Component: Frontend -> components/ui -> Skeleton primitive
 * Belongs to: the base UI kit (src/components/ui) — rendered as a loading placeholder
 * while a page's TanStack Query hooks are still fetching.
 * Purpose: a shimmering gray block standing in for content that hasn't loaded yet.
 */

import { cn } from "@/lib/utils";

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("relative overflow-hidden rounded-md bg-muted", className)}
      {...props}
    >
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-black/5 to-transparent dark:via-white/5" />
    </div>
  );
}
