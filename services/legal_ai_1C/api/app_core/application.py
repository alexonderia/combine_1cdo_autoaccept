"""Сборка FastAPI-приложения Legal AI."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI

from .config import settings, Settings


@dataclass(slots=True)
class AppContainer:
    """Контейнер для зависимостей приложения."""

    settings: Settings


def build_container() -> AppContainer:
    """Возвращает контейнер с глобальными настройками."""

    return AppContainer(settings=settings)


def create_app() -> FastAPI:
    """Создаёт приложение, регистрирует маршруты и startup-процедуры."""

    container = build_container()

    app = FastAPI(title="Legal AI Backend", version="0.5.0")
    app.state.container = container

    from .api import register_routers
    from .startup import register_startup

    register_routers(app)
    register_startup(app)
    return app
