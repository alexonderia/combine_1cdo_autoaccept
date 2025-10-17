"""Сборка и конфигурация FastAPI-приложения Globas."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI
from sqlalchemy.engine import Engine

from .db import engine as db_engine, ensure_schema


@dataclass(slots=True)
class AppContainer:
    """Минимальный контейнер зависимостей приложения."""

    engine: Engine


def build_container() -> AppContainer:
    """Инициализирует подключение к базе и гарантирует схему."""

    ensure_schema()
    return AppContainer(engine=db_engine)


def create_app() -> FastAPI:
    """Создаёт приложение и регистрирует маршруты."""

    container = build_container()

    app = FastAPI(
        title="Synthetic Globas API",
        version="0.1.0",
        description="API для генерации и проверки синтетических данных о контрагентах",
    )
    app.state.container = container

    from .api import register_routers

    register_routers(app)

    return app
