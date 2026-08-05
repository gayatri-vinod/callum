from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "callum"
    environment: str = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    database_url: str = "postgresql+asyncpg://callum:callum@localhost:5432/callum"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "callum"
    minio_secret_key: str = "callumsecret"
    minio_bucket: str = "callum"
    minio_secure: bool = False

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    upload_dir: str = "./data/uploads"
    max_upload_mb: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
