"""Маршруты для проверки состояния сервисов (локальная версия)."""

from fastapi import APIRouter, HTTPException
import httpx
from typing import Dict, Any, List
from config import settings

router = APIRouter()

async def check_service_health(url: str, service_name: str) -> Dict[str, Any]:
    """Проверяет состояние сервиса."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/health")
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": service_name,
                    "url": url,
                    "status": "ok",
                    "version": data.get("version", "N/A"),
                    "details": data
                }
            else:
                return {
                    "name": service_name,
                    "url": url,
                    "status": "error",
                    "version": "N/A",
                    "details": {"error": f"HTTP {response.status_code}"}
                }
    except Exception as e:
        return {
            "name": service_name,
            "url": url,
            "status": "down",
            "version": "N/A",
            "details": {"error": str(e)}
        }

@router.get("/status")
async def get_services_status() -> List[Dict[str, Any]]:
    """Возвращает статус всех сервисов."""
    services = [
        (settings.contract_extractor_url, "Contract Extractor"),
        (settings.globas_api_url, "Globas API"),
        (settings.legal_ai_url, "Legal AI")
    ]
    
    results = []
    for url, name in services:
        result = await check_service_health(url, name)
        results.append(result)
    
    return results

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Проверка состояния админ-панели."""
    return {"status": "ok", "service": "admin-panel-local"}
