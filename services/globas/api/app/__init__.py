"""Пакет FastAPI-приложения сервиса Globas."""

from .application import AppContainer, build_container, create_app

__all__ = ["AppContainer", "build_container", "create_app"]
