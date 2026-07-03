"""
Application configuration via Pydantic Settings.

Why Pydantic Settings?
- Type-safe environment variable parsing with validation at startup
- Fails fast if required config is missing (no runtime surprises)
- Supports .env files, environment variables, and defaults
- Generates documentation-friendly schemas

Why not python-dotenv directly?
- No type validation (everything is a string)
- No nested config support
- No startup validation
"""

from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings have sensible development defaults. In production,
    override via environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --------------------------------------------------------------------------
    # General
    # --------------------------------------------------------------------------
    environment: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"
    log_format: str = "console"  # "console" or "json"

    # --------------------------------------------------------------------------
    # Backend Server
    # --------------------------------------------------------------------------
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_workers: int = 1
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # --------------------------------------------------------------------------
    # Authentication (single-user mode for Phase 1)
    # --------------------------------------------------------------------------
    api_key: str = "dev-api-key-change-in-production"

    # --------------------------------------------------------------------------
    # PostgreSQL
    # --------------------------------------------------------------------------
    postgres_user: str = "raguser"
    postgres_password: str = "ragpassword"
    postgres_db: str = "rag_chatbot"
    postgres_host: str = "postgres"
    postgres_port: int = 5433

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Construct the async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url_sync(self) -> str:
        """Construct the sync PostgreSQL URL (for Alembic migrations)."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # --------------------------------------------------------------------------
    # Qdrant
    # --------------------------------------------------------------------------
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_collection_name: str = "documents"

    # --------------------------------------------------------------------------
    # Ollama
    # --------------------------------------------------------------------------
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:9b-q4_K_M"
    ollama_timeout: int = 120

    # LLM generation parameters
    llm_temperature: float = 0.7
    llm_top_p: float = 0.9
    llm_max_tokens: int = 2048

    # --------------------------------------------------------------------------
    # Embedding Model
    # --------------------------------------------------------------------------
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 32
    embedding_use_fp16: bool = False

    # --------------------------------------------------------------------------
    # Reranker Model
    # --------------------------------------------------------------------------
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"
    reranker_device: str = "cpu"
    reranker_use_fp16: bool = False

    # --------------------------------------------------------------------------
    # RAG Pipeline
    # --------------------------------------------------------------------------
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50
    rag_retrieval_top_k: int = 20
    rag_rerank_top_k: int = 5

    # --------------------------------------------------------------------------
    # Document Upload
    # --------------------------------------------------------------------------
    upload_dir: str = "/app/uploads"
    upload_max_size_mb: int = 50
    upload_allowed_extensions: str = "pdf,docx,pptx,txt,md,html"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def upload_max_size_bytes(self) -> int:
        """Convert MB to bytes for file size validation."""
        return self.upload_max_size_mb * 1024 * 1024

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_extensions_set(self) -> set[str]:
        """Parse comma-separated extensions into a set."""
        return {ext.strip().lower() for ext in self.upload_allowed_extensions.split(",")}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


def get_settings() -> Settings:
    """
    Get application settings.

    Settings are instantiated fresh each call to allow for
    environment variable changes during development.
    """
    return Settings()
