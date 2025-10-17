"""Сборка FastAPI-приложения для сервиса извлечения контрактных данных."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI

from .core.config import CONFIG
from .core.field_settings import FieldSettings
from .core.schema import load_schema
from .core.validator import SchemaValidator
from .services.extractor.pipeline import ExtractionPipeline
from .services.ollama_client import OllamaClient

APP_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = APP_DIR / "assets" / "schema.json"
SYSTEM_PROMPT_PATH = APP_DIR / "prompts" / "system.txt"
USER_TMPL_PATH = APP_DIR / "prompts" / "user_template.txt"
FIELD_GUIDELINES_PATH = APP_DIR / "prompts" / "field_guidelines.md"
SUMMARY_SYSTEM_PROMPT_PATH = APP_DIR / "prompts" / "summary_system.txt"
SUMMARY_USER_TMPL_PATH = APP_DIR / "prompts" / "summary_user_template.txt"
FIELD_PROMPTS_DIR = APP_DIR / "prompts" / "fields"
FIELD_EXTRACTORS_PATH = APP_DIR / "assets" / "field_extractors.json"
FIELD_CONTEXTS_PATH = APP_DIR / "assets" / "field_contexts.json"


@dataclass(slots=True)
class AppContainer:
    """Хранилище зависимостей, доступных обработчикам приложения."""

    config: Any
    schema: Dict[str, Any]
    raw_schema: Dict[str, Any]
    validator: SchemaValidator
    pipeline: ExtractionPipeline
    client: OllamaClient
    field_settings: FieldSettings


def _build_pipeline(raw_schema: Dict[str, Any], field_settings: FieldSettings) -> ExtractionPipeline:
    """Создаёт и настраивает конвейер извлечения."""

    return ExtractionPipeline(
        raw_schema,
        str(SYSTEM_PROMPT_PATH),
        str(USER_TMPL_PATH),
        field_settings,
        str(FIELD_GUIDELINES_PATH),
        str(SUMMARY_SYSTEM_PROMPT_PATH),
        str(SUMMARY_USER_TMPL_PATH),
    )


def build_container() -> AppContainer:
    """Инициализирует все необходимые сервисы и возвращает контейнер."""

    raw_schema = load_schema(str(SCHEMA_PATH))
    field_settings = FieldSettings(
        str(FIELD_EXTRACTORS_PATH),
        str(FIELD_GUIDELINES_PATH),
        str(FIELD_PROMPTS_DIR),
        str(FIELD_CONTEXTS_PATH),
    )
    enriched_schema = field_settings.apply_to_schema(raw_schema)
    validator = SchemaValidator(enriched_schema)
    pipeline = _build_pipeline(raw_schema, field_settings)
    client = OllamaClient()

    return AppContainer(
        config=CONFIG,
        schema=enriched_schema,
        raw_schema=raw_schema,
        validator=validator,
        pipeline=pipeline,
        client=client,
        field_settings=field_settings,
    )


def create_app() -> FastAPI:
    """Создаёт экземпляр FastAPI и регистрирует маршруты."""

    container = build_container()

    app = FastAPI(
        title="Contract Extractor API",
        version=container.config.version,
    )
    app.state.container = container

    from .api import register_routers

    register_routers(app)

    return app
