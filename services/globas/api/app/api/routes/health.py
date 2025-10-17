"""Маршруты проверки доступности сервиса."""

from fastapi import APIRouter, Depends
from sqlalchemy import text

from ...dependencies import container_dependency
from ...application import AppContainer

router = APIRouter(tags=["health"])


@router.get("/health")
def health(container: AppContainer = Depends(container_dependency)) -> dict:
    """Проверяет соединение с базой данных."""

    with container.engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"ok": True}
