/**
 * Component: Frontend -> components -> App layout shell
 * Belongs to: wraps every page's content in app/layout.tsx (inside AccessGate).
 * Purpose: the persistent page chrome — a fixed sidebar (desktop) or slide-over sidebar
 * (mobile, via a hamburger menu in the header) plus the top Header, with page content
 * rendered into the scrollable main area.
 */

"use client";

import { X } from "lucide-react";
import * as React from "react";

import { Header } from "@/components/header";
import { Sidebar } from "@/components/sidebar";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = React.useState(false);

  return (
    <div className="flex h-full">
      <aside className="hidden w-60 shrink-0 lg:block">
        <div className="fixed inset-y-0 left-0 w-60">
          <Sidebar />
        </div>
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 w-60">
            <Sidebar onNavigate={() => setMobileOpen(false)} />
            <button
              className="absolute right-3 top-3 text-white/70"
              onClick={() => setMobileOpen(false)}
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}

      <div className={cn("flex min-w-0 flex-1 flex-col")}>
        <Header onMenu={() => setMobileOpen(true)} />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-7xl p-4 sm:p-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
