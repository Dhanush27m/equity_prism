/**
 * Component: Frontend -> components -> Root providers
 * Belongs to: mounted once in app/layout.tsx, wrapping the entire app.
 * Purpose: sets up the two pieces of app-wide client state every page needs — a
 * TanStack Query client (server-state cache/refetching) and a light/dark theme context
 * (persisted to localStorage, defaulting to the OS preference on first visit) — then
 * renders AccessGate so no page content mounts before the access-key gate resolves.
 */

"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as React from "react";

import { AccessGate } from "@/components/access-gate";

type Theme = "light" | "dark";

const ThemeContext = React.createContext<{ theme: Theme; toggle: () => void }>({
  theme: "dark",
  toggle: () => {},
});

export function useTheme() {
  return React.useContext(ThemeContext);
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = React.useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30000, retry: 1, refetchOnWindowFocus: false },
        },
      })
  );
  const [theme, setTheme] = React.useState<Theme>("dark");
  const [mounted, setMounted] = React.useState(false);

  // Resolves the initial theme after mount (avoids SSR/client mismatch): stored
  // preference first, else the OS's prefers-color-scheme.
  React.useEffect(() => {
    const stored = (typeof localStorage !== "undefined" &&
      (localStorage.getItem("theme") as Theme | null)) || null;
    const initial =
      stored ??
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    setTheme(initial);
    setMounted(true);
  }, []);

  // Syncs the `.dark` class on <html> and persists the choice whenever it changes.
  React.useEffect(() => {
    if (!mounted) return;
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("theme", theme);
  }, [theme, mounted]);

  const toggle = React.useCallback(() => {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      <QueryClientProvider client={client}>
        <AccessGate>{children}</AccessGate>
      </QueryClientProvider>
    </ThemeContext.Provider>
  );
}
