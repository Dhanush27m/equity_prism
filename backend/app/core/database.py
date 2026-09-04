"""
Component: Backend -> Core -> Database
Belongs to: imported by every route/service/agent that talks to Postgres (via the
get_db FastAPI dependency or AsyncSessionLocal directly).
Purpose: builds the single async SQLAlchemy engine/session factory the whole app shares,
with connect-args that make it safe to run against Supabase's pgbouncer transaction
pooler (DB_POOLED) and its SSL requirement (DB_SSL) in the hosted profile.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()


# Builds asyncpg connect_args for the current profile. When DB_POOLED is true (Supabase's
# transaction pooler), asyncpg's prepared-statement caching must be disabled — a pooled
# connection can be handed to a different logical session between queries, and a cached
# "prepared statement already exists" would otherwise error. When DB_SSL is true, uses a
# non-verifying SSL context (Supabase's pooler terminates TLS itself).
def _connect_args() -> dict:
    args: dict = {}
    if settings.db_pooled:
        args["statement_cache_size"] = 0
        args["prepared_statement_cache_size"] = 0
    if settings.db_ssl:
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        args["ssl"] = ctx
    return args


# The shared async engine. pool_pre_ping=True means a stale/dropped connection (e.g.
# after Supabase resumes from a pause) is detected and transparently replaced rather than
# surfacing as a query error.
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args=_connect_args(),
)

# Session factory every request uses. expire_on_commit=False keeps loaded attributes
# readable after commit, which several routes rely on when returning the just-committed row.
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# FastAPI dependency: yields one request-scoped AsyncSession, closed automatically when
# the request finishes (via the `async with` context manager).
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
