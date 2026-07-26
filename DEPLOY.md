# Deploying Equity Prism for free (shareable public link)

This guide hosts Equity Prism at **$0** using:

| Piece | Service | Free? |
|---|---|---|
| Frontend (Next.js) | **Vercel** | ✅ |
| Backend + RAG (FastAPI, embeddings) | **Hugging Face Spaces** (Docker, 16 GB RAM) | ✅ |
| Postgres + pgvector | **Supabase** | ✅ |
| LLM | **Groq** | ✅ |
| Tracing (optional) | **LangFuse Cloud** | ✅ |

The **same code** runs locally and hosted — the cloud behaviour is switched on entirely by environment variables (see [.env.example](./.env.example), "Hosted profile"). Your local `docker compose` setup is untouched.

> ⚠️ **Before sharing publicly:** set an `ACCESS_KEY` (below). Without it, anyone with the link can use the app and spend your Groq quota.

---

## What changes in the hosted profile (already built in)

- **No Redis** → in-process caching (`CACHE_BACKEND=memory`)
- **No Celery worker** → PDF ingestion runs as a FastAPI background task (`INGEST_MODE=background`)
- **No Ollama** → Groq only (the app degrades gracefully if the fallback is absent)
- **No TimescaleDB** → only `pgvector` is required; the initial migration enables it automatically
- **Supabase pooler** → asyncpg runs with `statement_cache_size=0` (`DB_POOLED=true`, `DB_SSL=true`)
- **Cross-origin frontend** → the browser calls the backend by absolute URL (`NEXT_PUBLIC_API_BASE`)
- **Access gate** → optional shared password (`ACCESS_KEY` backend, `NEXT_PUBLIC_REQUIRE_ACCESS_KEY=1` frontend)

---

## Step 1 — Supabase (database)

1. Create a project at https://supabase.com (pick a region near you; save the database password).
2. **Database → Extensions →** enable **`vector`** (the migration also does this, but enabling it up front avoids surprises).
3. **Project Settings → Database → Connection string.** You need two forms of the **pooler** connection (Transaction mode, port `6543`, host `...pooler.supabase.com`):
   - **Async (app):**
     `postgresql+asyncpg://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres`
   - **Sync (migrations/seed):** use port `5432` (session mode) with SSL:
     `postgresql+psycopg://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require`

## Step 2 — Seed the database from YOUR machine

Do this locally — your home IP is far more reliable for yfinance than a datacenter. Point the sync/async URLs at Supabase and run the existing scripts:

```bash
# From the project root, in a shell where these env vars are set to your Supabase URLs:
export DATABASE_URL="postgresql+asyncpg://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:6543/postgres"
export DATABASE_URL_SYNC="postgresql+psycopg://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require"
export DB_POOLED=true DB_SSL=true

cd backend
pip install -r requirements.txt          # or reuse the backend container / a venv
alembic upgrade head                      # creates all tables + pgvector + HNSW/GIN indexes
python -m app.seed.seed_companies         # 50 Nifty stocks
python -m app.services.refresh            # metrics + risk signals (~5-7 min)
```

Verify in the Supabase table editor that `companies` has 50 rows.

## Step 3 — Hugging Face Space (backend)

1. Create a **Space** at https://huggingface.co/new-space → **SDK: Docker**, **Blank**. Make it **Public** (private Spaces sleep more aggressively) — the access gate protects it.
2. Put the **backend** into the Space repo. Easiest: clone the Space, copy the contents of this repo's `backend/` into it, and rename **`Dockerfile.hf` → `Dockerfile`**.
3. Add a `README.md` to the Space root with this frontmatter so HF knows the port:

   ```yaml
   ---
   title: Equity Prism API
   sdk: docker
   app_port: 7860
   ---
   ```
4. **Space → Settings → Variables and secrets**, add these **secrets**:

   | Name | Value |
   |---|---|
   | `DATABASE_URL` | your Supabase **async** URL (port 6543) |
   | `DATABASE_URL_SYNC` | your Supabase **sync** URL (port 5432, `?sslmode=require`) |
   | `GROQ_API_KEY` | your Groq key |
   | `DB_POOLED` | `true` |
   | `DB_SSL` | `true` |
   | `ACCESS_KEY` | a password you choose (e.g. a random string) |
   | `CORS_ORIGINS` | your Vercel URL, e.g. `https://equity-prism.vercel.app` |
   | `RUN_MIGRATIONS` | `0` (you already migrated in Step 2) |
   | `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` | *(optional)* LangFuse Cloud keys |

   `CACHE_BACKEND=memory`, `INGEST_MODE=background`, and the writable cache/upload dirs are already baked into `Dockerfile.hf`.
5. The Space builds automatically. First build takes a while (installs CPU torch + deps). When it's running, your backend base URL is:
   `https://<your-username>-<space-name>.hf.space`
   Check `https://<...>.hf.space/api/health` → should return `{"status":"ok"}`.

## Step 4 — Vercel (frontend)

1. Push this repo to GitHub (if you haven't).
2. At https://vercel.com → **New Project** → import the repo → set **Root Directory** to `frontend`.
3. **Environment Variables:**

   | Name | Value |
   |---|---|
   | `NEXT_PUBLIC_API_BASE` | your HF Space base URL, e.g. `https://<user>-<space>.hf.space` |
   | `NEXT_PUBLIC_REQUIRE_ACCESS_KEY` | `1` (shows the password gate) |

4. **Deploy.** Vercel gives you `https://<project>.vercel.app`.
5. Go back to the HF Space secrets and make sure `CORS_ORIGINS` is exactly that Vercel URL, then restart the Space (Settings → Factory reboot).

## Step 5 — Try it

Open your Vercel URL → enter the `ACCESS_KEY` at the gate → the app loads and talks to the HF backend, which reads/writes Supabase. Chat streams from Groq.

---

## Known limitations (free tier)

- **Cold start:** the HF Space sleeps after ~48 h idle; the first visit takes ~30–60 s to wake and load the embedding models. Uploaded-PDF *files* on the Space are ephemeral (reset on restart), but their extracted **chunks live in Supabase**, so document Q&A keeps working after a restart.
- **Supabase free pauses after ~7 days idle** — visit the dashboard weekly (or click your app) to keep it awake.
- **yfinance from HF IPs** may be throttled; the seeded data still displays, only live refreshes are affected. Re-run `app.services.refresh` from your machine to update prices.
- **Groq free rate limits** are fine for demo traffic; heavy use will throttle.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Frontend loads but every call fails | `NEXT_PUBLIC_API_BASE` wrong, or `CORS_ORIGINS` on the Space doesn't match the Vercel URL |
| 401 on every request | `ACCESS_KEY` mismatch — the gate password must equal the Space's `ACCESS_KEY` |
| Backend build fails / OOM | HF build limit — the `Dockerfile.hf` already uses CPU-only torch to stay small; retry the build |
| `prepared statement` errors | `DB_POOLED` must be `true` when using Supabase's pooler |
| Migrations didn't run | set `RUN_MIGRATIONS=1` on the Space once, or run `alembic upgrade head` locally against Supabase |
