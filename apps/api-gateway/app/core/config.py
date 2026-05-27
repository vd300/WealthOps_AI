from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    qdrant_url: str = Field(alias="QDRANT_URL")
    object_storage_url: str = Field(alias="OBJECT_STORAGE_URL")
    jwt_secret: SecretStr = Field(alias="JWT_SECRET")
    llm_provider: str = Field(alias="LLM_PROVIDER")
    llm_api_key: SecretStr = Field(alias="LLM_API_KEY")
    llm_model: str = Field(default="mock-rag-local", alias="LLM_MODEL")

    app_env: str = Field(default="local", alias="APP_ENV")
    service_name: str = Field(default="api-gateway", alias="SERVICE_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    service_check_timeout_seconds: float = Field(
        default=2.0,
        alias="SERVICE_CHECK_TIMEOUT_SECONDS",
        gt=0,
    )
    document_max_file_size_bytes: int = Field(
        default=10 * 1024 * 1024,
        alias="DOCUMENT_MAX_FILE_SIZE_BYTES",
        gt=0,
    )
    document_chunk_size: int = Field(
        default=1200,
        alias="DOCUMENT_CHUNK_SIZE",
        gt=0,
    )
    document_chunk_overlap: int = Field(
        default=200,
        alias="DOCUMENT_CHUNK_OVERLAP",
        ge=0,
    )
    object_storage_access_key: str = Field(
        default="minioadmin",
        alias="OBJECT_STORAGE_ACCESS_KEY",
    )
    object_storage_secret_key: SecretStr = Field(
        default=SecretStr("minioadmin"),
        alias="OBJECT_STORAGE_SECRET_KEY",
    )
    object_storage_bucket: str = Field(
        default="wealthops-documents",
        alias="OBJECT_STORAGE_BUCKET",
    )
    qdrant_collection_name: str = Field(
        default="document_chunks",
        alias="QDRANT_COLLECTION_NAME",
    )
    embedding_provider: str = Field(default="mock", alias="EMBEDDING_PROVIDER")
    embedding_dimensions: int = Field(
        default=384,
        alias="EMBEDDING_DIMENSIONS",
        gt=0,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
