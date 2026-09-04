/**
 * Component: Frontend -> components -> Top bar
 * Belongs to: rendered by app-shell.tsx on every page.
 * Purpose: the sticky top bar — a debounced stock search-and-navigate box (backed by
 * GET /api/companies?search=) and the light/dark theme toggle. On mobile also renders
 * the hamburger button that opens the slide-over sidebar.
 */

"use client";

import { Menu, Moon, Search, Sun } from "lucide-react";
import { useRouter } from "next/navigation";
import * as React from "react";

import { useTheme } from "@/components/providers";
import { Button } from "@/components/ui/button";
import { useCompanies } from "@/lib/hooks";
import { cn } from "@/lib/utils";

// Debounced (200ms) autocomplete search box: as the user types, queries
// GET /api/companies?search=..., shows up to 8 matches in a dropdown navigable by
// arrow keys/Enter, and navigates to the Company page on selection. Closes on
// outside-click via a document-level mousedown listener.
function StockSearch() {
  const router = useRouter();
  const [q, setQ] = React.useState("");
  const [debounced, setDebounced] = React.useState("");
  const [open, setOpen] = React.useState(false);
  const [active, setActive] = React.useState(0);
  const boxRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const t = setTimeout(() => setDebounced(q), 200);
    return () => clearTimeout(t);
  }, [q]);

  const { data } = useCompanies(debounced ? { search: debounced } : {});
  const results = (debounced ? data ?? [] : []).slice(0, 8);

  React.useEffect(() => {
    function onClick(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  function go(symbol: string) {
    setOpen(false);
    setQ("");
    router.push(`/company/${symbol}`);
  }

  return (
    <div ref={boxRef} className="relative w-full max-w-md">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
            setActive(0);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => {
            if (!results.length) return;
            if (e.key === "ArrowDown") setActive((a) => Math.min(a + 1, results.length - 1));
            else if (e.key === "ArrowUp") setActive((a) => Math.max(a - 1, 0));
            else if (e.key === "Enter") go(results[active].symbol);
          }}
          placeholder="Search stocks (e.g. RELIANCE, TCS)…"
          className="h-9 w-full rounded-md border border-input bg-card pl-9 pr-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>
      {open && results.length > 0 && (
        <div className="absolute z-50 mt-1 w-full overflow-hidden rounded-md border border-border bg-card shadow-lg">
          {results.map((c, i) => (
            <button
              key={c.symbol}
              onClick={() => go(c.symbol)}
              onMouseEnter={() => setActive(i)}
              className={cn(
                "flex w-full items-center justify-between px-3 py-2 text-left text-sm",
                i === active ? "bg-muted" : ""
              )}
            >
              <span>
                <span className="font-medium">{c.symbol}</span>
                <span className="ml-2 text-xs text-muted-foreground">{c.name}</span>
              </span>
              <span className="text-xs text-muted-foreground">{c.sector ?? ""}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function Header({ onMenu }: { onMenu: () => void }) {
  const { theme, toggle } = useTheme();
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur">
      <Button variant="ghost" size="icon" className="lg:hidden" onClick={onMenu} aria-label="Menu">
        <Menu className="h-5 w-5" />
      </Button>
      <StockSearch />
      <div className="ml-auto flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme">
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </div>
    </header>
  );
}
