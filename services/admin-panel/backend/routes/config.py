"""Маршруты для управления конфигурацией сервисов."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

import httpx
from fastapi import APIRouter, HTTPException

from core.services import SERVICE_REGISTRY, get_service_by_key

router = APIRouter()


async def _fetch_config(service_key: str, endpoint: str) -> Dict[str, Any]:
    """Возвращает конфигурацию сервиса по указанному endpoint."""
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


async def _try_fetch(service_key: str, endpoint: str) -> Dict[str, Any]:
    """Пытается получить конфигурацию, возвращая ошибку в теле ответа."""
    service = get_service_by_key(service_key)
    if not service:
        return {"name": service_key, "config": {"error": "unknown service"}}

    url = service.build_url(endpoint)
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url)
        except httpx.RequestError as error:
            return {"name": service.name, "config": {"error": str(error)}}

    if response.status_code == httpx.codes.OK:
        return {"name": service.name, "config": response.json()}
    return {
        "name": service.name,
        "config": {"error": f"HTTP {response.status_code}"},
    }


@router.get("/list")
async def list_configs() -> List[Dict[str, Any]]:
    """Возвращает конфигурации всех сервисов."""
    endpoints = {
        "contract-extractor": "/config",
        "globas-api": "/health",
        "legal-ai": "/health",
    }
    results: List[Dict[str, Any]] = []
    for service in SERVICE_REGISTRY:
        endpoint = endpoints.get(service.key, "/health")
        results.append(await _try_fetch(service.key, endpoint))
    return results


@router.get("/contract-extractor")
async def get_contract_extractor_config() -> Dict[str, Any]:
    """Получает полную конфигурацию Contract Extractor."""
    return await _fetch_config("contract-extractor", "/config")


@router.get("/legal-ai")
async def get_legal_ai_config() -> Dict[str, Any]:
    """Получает конфигурацию Legal AI."""
    return await _fetch_config("legal-ai", "/health")
