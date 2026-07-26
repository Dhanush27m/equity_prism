# Equity Prism — Build Prompt for Claude Code

You are building **Equity Prism**, a full-stack AI-powered equity research platform for Indian stock markets (NSE/BSE). It uses a LangGraph multi-agent system where specialized AI agents analyze stocks, compare companies, track sentiment, manage portfolios, and answer questions over uploaded financial documents using RAG.

This is a LOCAL build. Everything runs on my machine via Docker Compose. No deployment.

---

## ISOLATION RULES (NON-NEGOTIABLE)

1. Work ONLY inside the `equity-prism/` project folder. Do not read, write, modify, or scan anything outside it. Pretend nothing else exists on my machine.
2. Do NOT use any MCP servers or MCP connections. None are available.
3. Do NOT assume any pre-existing accounts, API keys, global configs, or credentials exist anywhere. Every account and key will be created fresh. When you need one, stop and ask me.
4. Do NOT assume any global packages or CLIs are installed beyond: `git`, `docker`, `docker compose`, `node`, `npm`, `python3`, `pip`.
5. Do NOT install anything globally. No `npm install -g`, no `pip install` without a virtual environment. Everything stays inside `equity-prism/`.
6. All Docker resources (volumes, networks) must use a project-specific prefix (`equity-prism_`) to avoid conflicts.
7. Do NOT touch git at all — no `git init`, no `git config`, no `git add`, no `git commit`, no `git remote`. I handle all git operations myself.
8. Environment variables go in `equity-prism/.env` only. Do not create or modify any file outside this folder.
9. Do NOT assume or fabricate any personal information — my name, email, usernames, or any identity detail. If you need any such value, ask me.
10. If unsure whether an action violates isolation, ask me first.

---

## HOW TO WORK

- Do everything yourself. Write all code, create all files, install all deps, configure everything.
- Only stop and ask me when you need something only a human can provide: API keys, account signups, personal info.
- Build incrementally — complete one module, verify it works, then move to the next.
- No comments in code. Clean code only.
- Test as you go. After each module, run it and fix errors before proceeding.
- If you hit an error you cannot fix after 3 attempts, show me the error and what you tried.
- Do not ask for design preferences, color choices, library opinions, or architecture confirmations. Everything is specified below. Just build it.

---

## TECH STACK (locked — do not substitute)

**Backend:** FastAPI, LangGraph, SQLAlchemy (async), Alembic, Celery + Redis, pydantic-settings

**LLM:** Groq API (Llama 3.3 70B, free tier, primary) → Ollama (Llama 3.1 8B, local fallback on rate limit). On Groq 429 error: retry 3x with exponential backoff (1s, 2s, 4s), then fall back to Ollama automatically.

**Database:** PostgreSQL 16 + pgvector extension + TimescaleDB extension (all in one container using `timescale/timescaledb-ha:pg16` image). Relational data + vector embeddings + time-series in a single database.

**Cache/Queue:** Redis 7 (API caching + Celery broker)

**RAG pipeline:** pdfplumber for PDF extraction → LangChain RecursiveCharacterTextSplitter (1000 chunk size, 200 overlap) → sentence-transformers `all-MiniLM-L6-v2` for embeddings (runs locally, no API) → pgvector for storage/retrieval → hybrid search (vector cosine similarity + PostgreSQL full-text `tsvector/tsquery`) combined with RRF → cross-encoder `ms-marco-MiniLM-L-6-v2` for reranking (runs locally) → citation tracking (filename, page number, source text)

**Observability:** LangFuse self-hosted (Docker, `langfuse/langfuse:2` image) for LLM tracing. RAGAS library for RAG evaluation.

**Frontend:** Next.js 15 (App Router, TypeScript), Tailwind CSS, shadcn/ui, TradingView Lightweight Charts (candlestick/OHLCV), Recharts (general charts), TanStack Query, Zustand

**Data sources (all free):** yfinance (NSE stocks use `.NS` suffix, BSE use `.BO`, default to NSE), Google News RSS for sentiment, user-uploaded PDFs for RAG

---

## DOCKER COMPOSE SERVICES

| Service | Image | Port | Notes |
|---------|-------|------|-------|
| db | timescale/timescaledb-ha:pg16 | 5432 | PostgreSQL + pgvector + TimescaleDB, two databases: `equity-prism` (app) and `langfuse` (observability) |
| redis | redis:7-alpine | 6379 | Caching + Celery broker |
| ollama | ollama/ollama | 11434 | Pull `llama3.1:8b` after container starts |
| langfuse | langfuse/langfuse:2 | 3000 | Connects to the `langfuse` database on same PostgreSQL |
| backend | Build from backend Dockerfile | 8000 | FastAPI + Celery worker |

Frontend runs outside Docker via `npm run dev` (for hot reload).

---

## WHAT TO BUILD (7 Phases — follow this order)

### Phase 1 — Infrastructure
Set up Docker Compose with all services listed above. Create `.env.example` with all required env vars (placeholders). Create `.env` from it. Start all containers, verify health. Pull the Ollama model.

**ASK ME:** "I need your Groq API key. Sign up free at https://console.groq.com with a fresh email and paste the key."

### Phase 2 — Backend foundation
Set up the Python project inside `equity-prism/backend/` with a local virtual environment. Create the FastAPI app, database connection, and all ORM models needed for: companies (symbol, name, sector, industry, market cap, exchange), financial statements, portfolio holdings, documents and document chunks (with pgvector embedding column), watchlists, and a simple user model (no auth, just a default local user). Set up Alembic, run migrations.

Create a seed script that uses yfinance to populate the database with these 50 Nifty stocks:
RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, HINDUNILVR, SBIN, BHARTIARTL, ITC, KOTAKBANK, LT, AXISBANK, ASIANPAINT, MARUTI, HCLTECH, SUNPHARMA, TATAMOTORS, NTPC, ULTRACEMCO, BAJFINANCE, WIPRO, POWERGRID, ONGC, TATASTEEL, ADANIENT, ADANIPORTS, JSWSTEEL, TECHM, NESTLEIND, TITAN, BAJAJFINSV, INDUSINDBK, GRASIM, CIPLA, APOLLOHOSP, DRREDDY, COALINDIA, BPCL, EICHERMOT, HEROMOTOCO, DIVISLAB, TATACONSUM, SBILIFE, BRITANNIA, LTIM, HINDALCO, M&M, BAJAJ-AUTO, SHRIRAMFIN, HDFCLIFE

Create basic API routes: health check, list companies, get company by symbol. Dockerize the backend. Verify endpoints return real data.

### Phase 3 — Data layer
Build services that wrap yfinance to provide: historical OHLCV data (configurable interval and range), company info and fundamentals, quarterly/annual financial statements, and calculated financial ratios (ROE, ROA, ROCE, debt-to-equity, current ratio, margins, EPS growth, revenue growth, FCF yield).

Build a news service that parses Google News RSS for a given company and classifies relevance.

Build a stock screener that filters companies by market cap, sector, P/E, ROE, and dividend yield ranges.

Expose all of these through API routes. Verify with real data for at least 3 stocks.

### Phase 4 — Multi-agent system (the core)
Build an LLM factory that tries Groq first, falls back to Ollama on rate limit/failure.

Build a LangGraph multi-agent graph with these agents:

1. **Router** — classifies user query into one of: company analysis, comparison, sentiment, portfolio, document Q&A, general. Extracts any stock symbols mentioned.
2. **Company Analyst** — given a symbol, produces comprehensive analysis: financial health, growth metrics, risk flags, valuation assessment.
3. **Comparator** — given 2-5 symbols, produces side-by-side comparison with best/worst per metric and a recommendation.
4. **Sentiment Analyst** — given a symbol, fetches news, classifies each as bullish/neutral/bearish, computes overall sentiment score.
5. **Portfolio Intelligence** — given holdings list, computes portfolio value, P&L, sector allocation, concentration risk, rebalancing suggestions.
6. **Synthesizer** — takes specialist outputs and produces a coherent final response with citations.

The LangGraph flow: `START → Router → [conditional edge by query type] → Specialist Agent → Synthesizer → END`

Integrate LangFuse callback handler for tracing every agent call.

Create a chat API endpoint that returns SSE (Server-Sent Events) streaming:
- `data: {"type": "token", "content": "partial text"}`
- `data: {"type": "sources", "content": [...]}`
- `data: {"type": "done"}`

**ASK ME:** "I need your LangFuse keys. Open http://localhost:3000, create an account and a project called Equity Prism, then give me the Public Key and Secret Key from Project Settings → API Keys."

Verify all agents work by testing: "Analyze Reliance Industries", "Compare TCS and Infosys", "What's the sentiment on HDFC Bank?", "My portfolio: 10 RELIANCE at 2500, 5 TCS at 3600".

### Phase 5 — RAG pipeline
Build the complete document research pipeline:

1. **Ingestion** — accept PDF upload, extract text, chunk it, generate embeddings locally, store chunks with embeddings in pgvector. Run as a Celery async task so uploads don't block the API.
2. **Retrieval** — hybrid search combining pgvector cosine similarity and PostgreSQL full-text search, merged with Reciprocal Rank Fusion.
3. **Reranking** — cross-encoder model running locally re-scores and selects top chunks.
4. **Citation tracking** — trace which chunks were used in the answer, return source references (filename, page number, text snippet).

Build a Document Research agent that uses this pipeline. Add it to the LangGraph graph as the `document_qa` route.

API routes: upload document (multipart), list documents with status, delete document. Document Q&A goes through the same chat endpoint (router classifies it as document_qa).

Verify: upload a sample PDF, ask questions about it, confirm citations appear.

### Phase 6 — Frontend
Initialize a Next.js 15 project inside `equity-prism/frontend/` with TypeScript, Tailwind, App Router. Install shadcn/ui, TradingView Lightweight Charts, Recharts, TanStack Query, Zustand, lucide-react. All deps local to `frontend/node_modules/`.

Proxy API calls to backend via next.config.ts rewrites (`/api/*` → `http://localhost:8000/api/*`). If LangFuse occupies port 3000, use a different port for the frontend.

Build these pages:

1. **Dashboard** — market indices cards (NIFTY 50, SENSEX, BANK NIFTY, INDIA VIX with current value + day change), watchlist table (stock, price, change%, sentiment badge), portfolio summary card (total value, P&L, sector allocation bar), quick-ask input.

2. **Company Detail** (`/company/[symbol]`) — TradingView candlestick chart with volume bars and time range selector (1M/3M/6M/1Y/5Y), key metrics cards row, financial statements tables (tabbed: income/balance/cashflow, toggleable quarterly/annual), risk flags section, "Ask AI" button linking to chat.

3. **Prism Chat** — full-height chat interface with message bubbles, SSE streaming (tokens appear in real-time), collapsible sources/citations below AI messages, suggested prompts when empty, chat history in sidebar (Zustand + localStorage).

4. **Compare** — multi-select stock picker (2-5 stocks), comparison triggered via chat agent, auto-generated data cards and bar charts comparing key metrics.

5. **Portfolio** — add/remove holdings form, holdings table with live P&L, portfolio metric cards, sector allocation donut chart, "Analyze Portfolio" button triggering the portfolio agent.

6. **Documents** — drag-and-drop PDF upload with progress, uploaded documents list with status, document Q&A chat with citations (filename + page number, expandable source text).

7. **Screener** — filter panel (sector, market cap range, P/E range, ROE range, dividend yield range), results table with sortable columns, click row → navigate to company detail.

8. **News & Sentiment** — overall market sentiment gauge, news feed with sentiment badges (bullish green / neutral gray / bearish red), filter by stock.

App shell: fixed sidebar with navigation to all pages + "Agent Traces" link pointing to LangFuse (localhost:3000) + Settings. Header with stock search bar (autocomplete) and dark mode toggle. Dark mode support throughout. Loading skeletons on all pages. Error states with retry. Responsive sidebar (collapsible on mobile).

### Phase 7 — Observability + polish
Ensure LangFuse tracing captures every agent call with trace ID, model, tokens, latency, cost.

Create an eval script: 5-10 test questions for the RAG pipeline, run RAGAS to compute faithfulness, answer relevancy, context precision scores. Print to console.

Add error handling: Groq fallback, yfinance failure graceful handling, upload failure status, frontend error toasts.

Write a comprehensive README with: project description, architecture diagram (text-based), tech stack table, features list, setup instructions (prerequisites, env vars, docker compose, seed, run frontend), agent architecture explanation, RAG pipeline explanation, RAGAS scores, API endpoint list, MIT license.

**ASK ME:** "Take screenshots of the running app and save them in `equity-prism/docs/screenshots/`. I'll reference them in the README."

---

## WHEN TO STOP AND ASK ME

1. Any API key or account signup needed (Groq, LangFuse, or anything else).
2. Any personal information (name, email, username) needed for any config.
3. Screenshots for README.
4. If an error persists after 3 fix attempts.
5. Nothing else. Build it.

---

Start now. Begin with Phase 1.
