"""Регистрация маршрутов FastAPI для Legal AI."""

from fastapi import FastAPI

from ..routes import analyze, connectivity, doc, health, ingest


def register_routers(app: FastAPI) -> None:
    """Подключает все роутеры к приложению."""

    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(analyze.router)
    app.include_router(connectivity.router)
    app.include_router(doc.router)
