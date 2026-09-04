/**
 * Component: Frontend -> components -> Navigation sidebar
 * Belongs to: rendered by app-shell.tsx (fixed on desktop, slide-over on mobile).
 * Purpose: the primary navigation between the app's 9 screens, highlighting the active
 * route, plus an optional "Agent Traces" link to LangFuse (only shown when
 * NEXT_PUBLIC_TRACES_URL is configured — hidden entirely otherwise) and a link to Settings.
 */

"use client";

import {
  BarChart3,
  FileText,
  GitCompareArrows,
  LayoutDashboard,
  LineChart,
  MessageSquare,
  Newspaper,
  Activity,
  Briefcase,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const TRACES_URL = process.env.NEXT_PUBLIC_TRACES_URL;

// The main nav — one entry per top-level page (Dashboard is "/", everything else its
// own route). Settings is rendered separately below since it sits in its own footer group.
const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/chat", label: "Prism Chat", icon: MessageSquare },
  { href: "/screener", label: "Screener", icon: BarChart3 },
  { href: "/compare", label: "Compare", icon: GitCompareArrows },
  { href: "/portfolio", label: "Portfolio", icon: Briefcase },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/news", label: "News & Sentiment", icon: Newspaper },
];

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex h-14 items-center gap-2 px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
          <LineChart className="h-5 w-5 text-primary-foreground" />
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold text-white">Equity Prism</div>
          <div className="text-[10px] text-sidebar-foreground/60">Indian markets · AI research</div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-3">
        {NAV.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-sidebar-active text-white"
                  : "text-sidebar-foreground hover:bg-sidebar-active/60 hover:text-white"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="space-y-1 border-t border-white/5 px-3 py-3">
        {TRACES_URL && (
          <a
            href={TRACES_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-sidebar-foreground transition-colors hover:bg-sidebar-active/60 hover:text-white"
          >
            <Activity className="h-4 w-4 shrink-0" />
            Agent Traces
            <ExternalLink className="ml-auto h-3 w-3 opacity-60" />
          </a>
        )}
        <Link
          href="/settings"
          onClick={onNavigate}
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-sidebar-foreground transition-colors hover:bg-sidebar-active/60 hover:text-white"
        >
          <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          Settings
        </Link>
      </div>
    </div>
  );
}
