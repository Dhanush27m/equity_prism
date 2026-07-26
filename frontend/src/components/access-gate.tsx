"use client";

import { KeyRound } from "lucide-react";
import * as React from "react";

import { apiGet, getAccessKey, setAccessKey } from "@/lib/api";
import { Button } from "@/components/ui/button";

const REQUIRED = process.env.NEXT_PUBLIC_REQUIRE_ACCESS_KEY === "1";

export function AccessGate({ children }: { children: React.ReactNode }) {
  const [unlocked, setUnlocked] = React.useState(!REQUIRED);
  const [value, setValue] = React.useState("");
  const [error, setError] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    if (!REQUIRED) return;
    if (getAccessKey()) setUnlocked(true);
    const onUnauthorized = () => {
      setUnlocked(false);
      setError("Session expired. Enter the access key again.");
    };
    window.addEventListener("equity-prism-unauthorized", onUnauthorized);
    return () => window.removeEventListener("equity-prism-unauthorized", onUnauthorized);
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!value || busy) return;
    setBusy(true);
    setError("");
    setAccessKey(value.trim());
    try {
      await apiGet("/api/chat/agents");
      setUnlocked(true);
    } catch {
      setAccessKey("");
      setError("Incorrect access key.");
    } finally {
      setBusy(false);
    }
  }

  if (unlocked) return <>{children}</>;

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <form
        onSubmit={submit}
        className="w-full max-w-sm space-y-4 rounded-xl border border-border bg-card p-6 shadow-lg"
      >
        <div className="flex items-center gap-2">
          <KeyRound className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold">Equity Prism</h1>
        </div>
        <p className="text-sm text-muted-foreground">
          This is a private demo. Enter the access key to continue.
        </p>
        <input
          type="password"
          autoFocus
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Access key"
          className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        {error && <p className="text-sm text-negative">{error}</p>}
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? "Checking…" : "Unlock"}
        </Button>
      </form>
    </div>
  );
}
