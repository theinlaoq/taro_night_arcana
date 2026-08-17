"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the backend."""

    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    llm_base_url: str = "http://localhost:8001/v1"
    llm_api_key: str = "local-dev-key"
    llm_model: str = "local-model"
    llm_timeout_seconds: float = 20
    session_ttl_seconds: int = 600
    reversal_probability: float = 0.35

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """Return comma-separated CORS origins as a Starlette-compatible list."""
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return origins or ["http://127.0.0.1:5173", "http://localhost:5173"]


settings = Settings()
