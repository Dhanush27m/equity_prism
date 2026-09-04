/**
 * Component: Frontend -> components/ui -> Spinner primitive
 * Belongs to: the base UI kit (src/components/ui) — used inside buttons/inline loading
 * indicators (distinct from Skeleton, which stands in for whole content blocks).
 * Purpose: a small spinning loader icon.
 */

import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("h-4 w-4 animate-spin", className)} />;
}
