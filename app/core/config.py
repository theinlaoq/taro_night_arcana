"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the backend."""

    llm_base_url: str = "http://localhost:8001/v1"
    llm_api_key: str = "local-dev-key"
    llm_model: str = "local-model"
    llm_timeout_seconds: float = 20
    session_ttl_seconds: int = 600
    reversal_probability: float = 0.35

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
