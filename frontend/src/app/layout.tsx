/**
 * Component: Frontend -> app -> Root layout
 * Belongs to: Next.js App Router's mandatory root layout — wraps every page in the app.
 * Purpose: sets up fonts, page metadata, and a pre-hydration inline script that applies
 * the saved/OS theme to <html> before React mounts (avoids a light->dark flash on load),
 * then nests Providers (theme/query-client/access-gate) and AppShell (sidebar/header)
 * around the page content.
 */

import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { AppShell } from "@/components/app-shell";
import { Providers } from "@/components/providers";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Equity Prism — AI Equity Research",
  description: "Local AI-powered equity research for Indian markets (NSE/BSE).",
};

// Runs synchronously before paint (inline in <head>) so the correct theme class is on
// <html> from the very first frame — Providers' own theme effect runs after hydration
// and would otherwise cause a visible flash from the default theme to the real one.
const themeScript = `try{var t=localStorage.getItem('theme')||(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');document.documentElement.classList.toggle('dark',t==='dark');}catch(e){}`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="h-full">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
