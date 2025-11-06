"""Конфигурация админ-панели."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения FastAPI."""

    contract_extractor_url: str = Field(
        default="http://contract-extractor-api:8080",
        alias="CONTRACT_EXTRACTOR_URL",
        description="Базовый URL сервиса Contract Extractor",
    )
    globas_api_url: str = Field(
        default="http://globas-api:8000",
        alias="GLOBAS_API_URL",
        description="Базовый URL сервиса Globas API",
    )
    legal_ai_url: str = Field(
        default="http://legal-ai:8000",
        alias="LEGAL_AI_URL",
        description="Базовый URL сервиса Legal AI",
    )

    app_name: str = Field(default="Admin Panel (Local)")
    version: str = Field(default="1.0.0")
    debug: bool = Field(default=True, alias="DEBUG")
    port: int = Field(default=8001, alias="PORT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
