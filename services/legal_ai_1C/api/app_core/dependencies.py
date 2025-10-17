"""Общие зависимости FastAPI для получения контейнера приложения."""

from fastapi import Depends, Request

from .application import AppContainer


def get_container(request: Request) -> AppContainer:
    """Возвращает контейнер приложения."""

    container = getattr(request.app.state, "container", None)
    if container is None:  # pragma: no cover - защитная проверка
        raise RuntimeError("Контейнер не инициализирован")
    return container


def container_dependency(container: AppContainer = Depends(get_container)) -> AppContainer:
    """Позволяет использовать контейнер в Depends."""

    return container
