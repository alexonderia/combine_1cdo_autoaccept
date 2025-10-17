"""Общие зависимости FastAPI-приложения."""

from fastapi import Depends, Request

from .application import AppContainer


def get_container(request: Request) -> AppContainer:
    """Возвращает контейнер приложения из состояния FastAPI."""

    container = getattr(request.app.state, "container", None)
    if container is None:  # pragma: no cover - защитная проверка
        raise RuntimeError("Контейнер приложения не инициализирован")
    return container


def container_dependency(container: AppContainer = Depends(get_container)) -> AppContainer:
    """Фасад для явного использования в Depends."""

    return container
