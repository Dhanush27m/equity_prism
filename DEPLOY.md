# Deploying Equity Prism for free (shareable public link)

This is the setup Equity Prism actually runs on — all free tiers, $0/month:

| Piece | Service | Free? |
|---|---|---|
| Frontend (Next.js) | **Vercel** | ✅ |
| Backend + RAG (FastAPI) | **Render** (Docker web service) | ✅ |
| Postgres + pgvector | **Supabase** | ✅ |
| LLM | **Groq** | ✅ |
| Embeddings | **fastembed** (ONNX, in-process — no external service) | ✅ |
| Tracing (optional) | **LangFuse Cloud** | ✅ |

The cloud behaviour is switched on entirely by environment variables (see [.env.example](./.env.example), "Hosted profile") — the lightweight image (`backend/Dockerfile.light`) drops torch, Redis, Celery, and Ollama so it fits free tiers.

> ⚠️ **Before sharing publicly:** set an `ACCESS_KEY` (below). Without it, anyone with the link can use the app and spend your Groq quota.

---

## What the hosted profile does (already built in)

- **No torch** → embeddings use `fastembed` (ONNX all-MiniLM-L6-v2, 384-dim), the reranker is disabled (`EMBEDDING_BACKEND=fastembed`, `RERANK_ENABLED=false`). Keeps the image small enough for free hosting.
- **No Redis** → in-process caching (`CACHE_BACKEND=memory`)
- **No Celery worker** → PDF ingestion runs as a FastAPI background task (`INGEST_MODE=background`)
- **No Ollama** → Groq only
- **No TimescaleDB** → only `pgvector` is required; the initial migration enables it automatically
- **Supabase pooler** → asyncpg runs with `statement_cache_size=0` + non-verifying SSL (`DB_POOLED=true`, `DB_SSL=true`)
- **Cross-origin frontend** → the browser calls the backend by absolute URL (`NEXT_PUBLIC_API_BASE`)
- **Access gate** → shared password (`ACCESS_KEY` backend, `NEXT_PUBLIC_REQUIRE_ACCESS_KEY=1` frontend)

The lightweight image is built from **`backend/Dockerfile.light`** (declared in **`render.yaml`**).

---

## Step 1 — Supabase (database)

1. Create a project at https://supabase.com (pick a region near you; save the database password).
2. **Database → Extensions →** enable **`vector`**.
3. **Project Settings → Database → Connection string.** Grab the two **pooler** connection strings:
   - **Async (app), Transaction pooler, port 6543:**
     `postgresql+asyncpg://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres`
   - **Sync (migrations/seed), Session pooler, port 5432, with SSL:**
     `postgresql+psycopg://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require`

## Step 2 — Seed the database from YOUR machine

Do this from your own machine — a home IP is far more reliable for yfinance than a datacenter. From `backend/`, install the deps, point the env at Supabase, and run the seed scripts:

```bash
cd backend
pip install -r requirements.txt

# Point at Supabase (async URL for the app, sync URL for Alembic):
export DATABASE_URL='postgresql+asyncpg://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:6543/postgres'
export DATABASE_URL_SYNC='postgresql+psycopg://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require'
export DB_POOLED=true DB_SSL=true

alembic upgrade head
python -m app.seed.seed_companies
python -m app.services.refresh          # ~5-7 min
```

Verify in the Supabase table editor that `companies` has 50 rows. (This is a one-time step — the database is already seeded.)

## Step 3 — GitHub

Render deploys from a Git repo, so push this project to GitHub (`git push origin main`). The repo already contains `render.yaml` and `backend/Dockerfile.light`.

## Step 4 — Render (backend)

1. Go to https://render.com → **Sign in with GitHub**.
2. **New + → Blueprint** → select your repo. Render detects **`render.yaml`** and a service named **`equity-prism-api`**.
3. Fill in the secret env vars it prompts for:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | Supabase **async** URL (port 6543) |
   | `DATABASE_URL_SYNC` | Supabase **sync** URL (port 5432, `?sslmode=require`) |
   | `GROQ_API_KEY` | your Groq key |
   | `ACCESS_KEY` | a password you choose |

   `DB_POOLED`, `DB_SSL`, `CORS_ORIGINS`, `RUN_MIGRATIONS`, and the fastembed/cache settings are already set by `render.yaml` / the Dockerfile.
4. **Apply**. Render builds the lightweight image (~2-3 min) and starts it. Your backend URL is like `https://equity-prism-api.onrender.com`. Check `/api/health` → `{"status":"ok"}`.

## Step 5 — Vercel (frontend)

1. https://vercel.com → **Continue with GitHub** → **Add New → Project** → import the repo.
2. Set **Root Directory** to **`frontend`**.
3. Environment variables:

   | Name | Value |
   |---|---|
   | `NEXT_PUBLIC_API_BASE` | your Render URL, e.g. `https://equity-prism-api.onrender.com` |
   | `NEXT_PUBLIC_REQUIRE_ACCESS_KEY` | `1` |

4. **Deploy.** Vercel gives you `https://<project>.vercel.app` — that's your shareable link.
5. (Optional) In Render, set `CORS_ORIGINS` to the exact Vercel URL instead of `*`.

## Step 6 — Try it

Open your Vercel URL → enter the `ACCESS_KEY` at the gate → the app loads and talks to Render, which reads/writes Supabase and streams from Groq.

---

## Known limitations (free tier)

- **Cold start:** Render's free service sleeps after ~15 min idle; the first visit takes ~50–60 s to wake, and the first document-RAG query downloads the fastembed model (~20 s more). Normal for free hosting.
- **Supabase free pauses after ~7 days idle** — visit the app weekly to keep it awake.
- **yfinance from datacenter IPs** may be throttled; seeded data still displays. Re-run `app.services.refresh` from your machine to update prices.
- **Groq free rate limits** are fine for demo traffic.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Frontend loads but every call fails | `NEXT_PUBLIC_API_BASE` wrong, or `CORS_ORIGINS` on Render doesn't allow the Vercel URL |
| 401 on every request | `ACCESS_KEY` mismatch — the gate password must equal Render's `ACCESS_KEY` |
| `prepared statement` errors | `DB_POOLED` must be `true` when using Supabase's pooler |
| Migrations didn't run | run `alembic upgrade head` locally against Supabase (Step 2), or set `RUN_MIGRATIONS=1` on Render once |
