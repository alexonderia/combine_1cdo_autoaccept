"""Регистрация всех маршрутов сервиса Globas."""

from fastapi import FastAPI

from .routes import admin, company, health


def register_routers(app: FastAPI) -> None:
    """Подключает основные роутеры к приложению."""

    app.include_router(health.router)
    app.include_router(admin.router)
    app.include_router(company.router)
