"""Пакет FastAPI-приложения для сервиса извлечения данных."""

from .application import create_app, AppContainer, build_container

__all__ = ["create_app", "AppContainer", "build_container"]
