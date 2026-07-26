from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    database_url: str = ""
    database_url_sync: str = ""

    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    cache_backend: str = "redis"
    ingest_mode: str = "celery"
    db_pooled: bool = False
    db_ssl: bool = False
    access_key: str = ""
    cors_origins: str = "*"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://langfuse:3000"

    embedding_model: str = "all-MiniLM-L6-v2"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    embedding_backend: str = "local"
    hf_api_token: str = ""
    rerank_enabled: bool = True

    upload_dir: str = "/app/data/uploads"
    max_upload_mb: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
