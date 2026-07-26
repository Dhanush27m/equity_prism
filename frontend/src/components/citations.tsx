"use client";

import { ChevronDown, ExternalLink, FileText, Newspaper, BarChart2 } from "lucide-react";
import * as React from "react";

import { Badge } from "@/components/ui/badge";
import type { Citation } from "@/lib/types";

function icon(type?: string) {
  if (type === "document") return <FileText className="h-3.5 w-3.5" />;
  if (type === "news") return <Newspaper className="h-3.5 w-3.5" />;
  return <BarChart2 className="h-3.5 w-3.5" />;
}

export function Citations({ citations }: { citations: Citation[] }) {
  const [open, setOpen] = React.useState(false);
  if (!citations?.length) return null;

  return (
    <div className="mt-3 rounded-md border border-border bg-muted/30">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 px-3 py-2 text-xs font-medium text-muted-foreground"
      >
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
        {citations.length} source{citations.length > 1 ? "s" : ""}
      </button>
      {open && (
        <div className="space-y-2 px-3 pb-3">
          {citations.map((c, i) => (
            <div key={i} className="rounded-md border border-border bg-card p-2.5 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">{icon(c.type)}</span>
                <span className="font-medium">
                  {c.marker != null && <span className="mr-1 text-primary">[{c.marker}]</span>}
                  {c.label ?? c.filename ?? "Source"}
                </span>
                {c.page_number != null && (
                  <Badge variant="outline" className="ml-auto">
                    p.{c.page_number}
                  </Badge>
                )}
                {c.url && (
                  <a
                    href={c.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-auto text-primary"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                )}
              </div>
              {c.snippet && <p className="mt-1.5 text-muted-foreground">{c.snippet}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
