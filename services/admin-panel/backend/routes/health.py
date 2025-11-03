"""Маршруты для проверки состояния админ-панели и подключенных сервисов."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from core.services import fetch_all_services_health

router = APIRouter()


@router.get("/status")
async def get_services_status() -> List[Dict[str, Any]]:
    """Возвращает статус всех подключенных сервисов."""
    statuses = await fetch_all_services_health()
    return [status.as_dict() for status in statuses]


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Возвращает состояние самой админ-панели."""
    return {"status": "ok", "service": "admin-panel-local"}
