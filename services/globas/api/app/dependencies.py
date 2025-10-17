"""Зависимости FastAPI для доступа к контейнеру."""

from fastapi import Depends, Request

from .application import AppContainer


def get_container(request: Request) -> AppContainer:
    """Извлекает контейнер приложения из состояния FastAPI."""

    container = getattr(request.app.state, "container", None)
    if container is None:  # pragma: no cover - защитная проверка
        raise RuntimeError("Контейнер не инициализирован")
    return container


def container_dependency(container: AppContainer = Depends(get_container)) -> AppContainer:
    """Фасад для использования контейнера в Depends."""

    return container
