"""Маршруты для управления сервисами (локальная версия)."""

from fastapi import APIRouter, HTTPException
import httpx
from typing import Dict, Any, List
from config import settings

router = APIRouter()

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
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    data = response.json()
                    results.append({
                        "name": name,
                        "url": url,
                        "status": "ok",
                        "version": data.get("version", "N/A"),
                        "details": data
                    })
                else:
                    results.append({
                        "name": name,
                        "url": url,
                        "status": "error",
                        "version": "N/A",
                        "details": {"error": f"HTTP {response.status_code}"}
                    })
        except Exception as e:
            results.append({
                "name": name,
                "url": url,
                "status": "down",
                "version": "N/A",
                "details": {"error": str(e)}
            })
    
    return results

@router.get("/contract-extractor/config")
async def get_contract_extractor_config() -> Dict[str, Any]:
    """Получает конфигурацию Contract Extractor."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.contract_extractor_url}/config")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=502, detail="Contract Extractor недоступен")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ошибка подключения: {str(e)}")

@router.get("/contract-extractor/schema")
async def get_contract_extractor_schema() -> Dict[str, Any]:
    """Получает схему Contract Extractor."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.contract_extractor_url}/schema")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=502, detail="Contract Extractor недоступен")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ошибка подключения: {str(e)}")

@router.get("/contract-extractor/models")
async def get_contract_extractor_models() -> Dict[str, Any]:
    """Получает список моделей Contract Extractor."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.contract_extractor_url}/models")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=502, detail="Contract Extractor недоступен")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ошибка подключения: {str(e)}")
