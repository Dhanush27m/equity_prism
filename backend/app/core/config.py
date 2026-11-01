"""
Component: Backend -> Core -> Configuration
Belongs to: imported by nearly every backend module (`from app.core.config import
get_settings`) — the single source of truth for environment-driven behavior.
Purpose: defines every environment variable the app reads, with the "local-heavy" defaults
baked in (Redis cache, Celery ingestion, sentence-transformers embeddings, open access).
The hosted/free-tier deployment overrides a specific subset of these (see DEPLOY.md's
"hosted profile" table) purely via environment variables — no code branches on environment name.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# All app settings, loaded from environment variables (and .env locally). Every field's
# default is the local/self-hosted behavior; the hosted deployment's render.yaml supplies
# the overrides that switch it into the lightweight free-tier profile.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    database_url: str = ""
    database_url_sync: str = ""

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    cache_backend: str = "memory"
    ingest_mode: str = "background"
    db_pooled: bool = False
    db_ssl: bool = False
    cors_origins: str = "*"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    groq_api_key: str = ""
    groq_model: str = ""

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"

    embedding_model: str = "all-MiniLM-L6-v2"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    embedding_backend: str = "local"
    rerank_enabled: bool = True

    upload_dir: str = "./data/uploads"
    max_upload_mb: int = 30


# Cached singleton accessor — Settings() is constructed once per process and reused
# everywhere via get_settings(), avoiding re-parsing the environment on every call.
@lru_cache
def get_settings() -> Settings:
    return Settings()
