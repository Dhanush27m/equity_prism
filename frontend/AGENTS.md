# Equity Prism — Frontend

Next.js 15 (App Router, TypeScript, Tailwind v4), pinned to v15 to match the locked project stack. Runs on **port 3001** (LangFuse owns 3000). API calls to `/api/*` are proxied to the FastAPI backend at `http://localhost:8000` via `next.config.ts` rewrites.

Standard Next.js 15 conventions apply. Dark mode is class-based (`.dark` on `<html>`) via a Tailwind v4 `@custom-variant`. UI primitives live in `src/components/ui`.
