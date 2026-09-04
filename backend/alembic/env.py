"""
Component: Backend -> Data Layer -> Alembic migration runtime config
Belongs to: run via `alembic upgrade head` (locally, in DEPLOY.md's seeding step, or via
RUN_MIGRATIONS=1 on Render) — not part of the request-serving app itself.
Purpose: wires Alembic to the app's own settings (DATABASE_URL_SYNC) and model metadata
(app.models.Base) so migrations stay in sync with the SQLAlchemy models, and teaches
Alembic's autogenerate how to render a pgvector Vector column type correctly.
"""

from logging.config import fileConfig

import pgvector.sqlalchemy
from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import get_settings
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Always use the app's own sync database URL rather than whatever alembic.ini has —
# keeps one source of truth for the connection string.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

target_metadata = Base.metadata


# Teaches `alembic revision --autogenerate` how to emit a pgvector Vector(dim=...) column
# type in a generated migration file (without this, autogenerate wouldn't know how to
# render that custom SQLAlchemy type).
def render_item(type_, obj, autogen_context):
    if type_ == "type" and isinstance(obj, pgvector.sqlalchemy.Vector):
        autogen_context.imports.add("import pgvector.sqlalchemy")
        return f"pgvector.sqlalchemy.Vector(dim={obj.dim})"
    return False


# Generates SQL without a live DB connection (`alembic upgrade head --sql`).
def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url_sync,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


# Applies migrations against a real, live database connection — the normal path.
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
