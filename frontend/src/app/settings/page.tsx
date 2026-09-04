/**
 * Component: Frontend -> app -> Settings page (route "/settings")
 * Belongs to: linked from the sidebar footer.
 * Purpose: shows backend liveness (via GET /api/health), a theme toggle, and a link to
 * LangFuse for agent tracing. Note: the "API base" row and the LangFuse link below are
 * hardcoded to localhost — display-only holdovers from local development, not wired to
 * NEXT_PUBLIC_API_BASE/NEXT_PUBLIC_TRACES_URL like the rest of the app is.
 */

"use client";

import { Activity, ExternalLink, Moon, Server, Sun } from "lucide-react";

import { useTheme } from "@/components/providers";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useHealth } from "@/lib/hooks";

// A simple label/value row used throughout this page's info cards.
function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-border py-2 text-sm last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

export default function SettingsPage() {
  const { theme, toggle } = useTheme();
  const { data, isError } = useHealth();

  return (
    <div className="max-w-2xl space-y-5">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">Local environment & appearance</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-4 w-4" /> Backend
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <Row
            label="API status"
            value={
              isError ? (
                <span className="text-negative">Offline</span>
              ) : data ? (
                <span className="text-positive">Online</span>
              ) : (
                "…"
              )
            }
          />
          <Row label="Environment" value={data?.env ?? "local"} />
          <Row label="API base" value="/api → localhost:8000" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">Appearance</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="flex items-center justify-between py-2 text-sm">
            <span className="text-muted-foreground">Theme</span>
            <Button variant="outline" size="sm" onClick={toggle}>
              {theme === "dark" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
              {theme === "dark" ? "Dark" : "Light"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-4 w-4" /> Observability
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <p className="mb-3 text-sm text-muted-foreground">
            Agent traces (model, latency, tokens) are captured in LangFuse when keys are configured.
          </p>
          <a href="http://localhost:3000" target="_blank" rel="noopener noreferrer">
            <Button variant="outline" size="sm">
              Open LangFuse <ExternalLink className="h-3.5 w-3.5" />
            </Button>
          </a>
        </CardContent>
      </Card>
    </div>
  );
}
