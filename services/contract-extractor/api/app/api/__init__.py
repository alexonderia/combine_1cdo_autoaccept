"""Регистрация маршрутов FastAPI для сервиса контрактного извлечения."""

from fastapi import FastAPI

from .routes import extraction, health


def register_routers(app: FastAPI) -> None:
    """Подключает все роутеры к приложению."""

    app.include_router(health.router)
    app.include_router(extraction.router)
