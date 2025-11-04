"""Маршруты для получения информации о подключенных сервисах."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, HTTPException

from core.services import (
    SERVICE_REGISTRY,
    fetch_all_services_health,
    get_service_by_key,
)

router = APIRouter()


async def _get(service_key: str, endpoint: str) -> Dict[str, Any]:
    """Выполняет GET-запрос к сервису и возвращает ответ."""
    service = get_service_by_key(service_key)
    if not service:
        raise HTTPException(status_code=404, detail=f"Неизвестный сервис: {service_key}")

    url = service.build_url(endpoint)
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url)
        except httpx.RequestError as error:
            raise HTTPException(status_code=502, detail=f"Ошибка подключения: {error}") from error

    if response.status_code != httpx.codes.OK:
        raise HTTPException(status_code=502, detail=f"{service.name} недоступен")
    return response.json()


@router.get("/status")
async def get_services_status() -> List[Dict[str, Any]]:
    """Возвращает статус всех сервисов."""
    statuses = await fetch_all_services_health(SERVICE_REGISTRY)
    return [status.as_dict() for status in statuses]


@router.get("/contract-extractor/config")
async def get_contract_extractor_config() -> Dict[str, Any]:
    """Получает конфигурацию Contract Extractor."""
    return await _get("contract-extractor", "/config")


@router.get("/contract-extractor/schema")
async def get_contract_extractor_schema() -> Dict[str, Any]:
    """Получает схему Contract Extractor."""
    return await _get("contract-extractor", "/schema")


@router.get("/contract-extractor/models")
async def get_contract_extractor_models() -> Dict[str, Any]:
    """Получает список моделей Contract Extractor."""
    return await _get("contract-extractor", "/models")
