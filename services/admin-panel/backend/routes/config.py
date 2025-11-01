"""Маршруты для управления конфигурацией (локальная версия)."""

from fastapi import APIRouter, HTTPException
import httpx
from typing import Dict, Any, List
from config import settings

router = APIRouter()

@router.get("/list")
async def list_configs() -> List[Dict[str, Any]]:
    """Возвращает конфигурации всех сервисов."""
    configs = []
    
    # Contract Extractor конфигурация
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.contract_extractor_url}/config")
            if response.status_code == 200:
                configs.append({
                    "name": "Contract Extractor",
                    "config": response.json()
                })
            else:
                configs.append({
                    "name": "Contract Extractor",
                    "config": {"error": f"HTTP {response.status_code}"}
                })
    except Exception as e:
        configs.append({
            "name": "Contract Extractor", 
            "config": {"error": str(e)}
        })
    
    # Globas API конфигурация (базовая информация)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.globas_api_url}/health")
            if response.status_code == 200:
                configs.append({
                    "name": "Globas API",
                    "config": {
                        "status": "ok",
                        "database_connected": True
                    }
                })
            else:
                configs.append({
                    "name": "Globas API",
                    "config": {"error": f"HTTP {response.status_code}"}
                })
    except Exception as e:
        configs.append({
            "name": "Globas API",
            "config": {"error": str(e)}
        })
    
    # Legal AI конфигурация
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.legal_ai_url}/health")
            if response.status_code == 200:
                configs.append({
                    "name": "Legal AI",
                    "config": response.json()
                })
            else:
                configs.append({
                    "name": "Legal AI",
                    "config": {"error": f"HTTP {response.status_code}"}
                })
    except Exception as e:
        configs.append({
            "name": "Legal AI",
            "config": {"error": str(e)}
        })
    
    return configs

@router.get("/contract-extractor")
async def get_contract_extractor_config() -> Dict[str, Any]:
    """Получает полную конфигурацию Contract Extractor."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.contract_extractor_url}/config")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=502, detail="Contract Extractor недоступен")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ошибка подключения: {str(e)}")

@router.get("/legal-ai")
async def get_legal_ai_config() -> Dict[str, Any]:
    """Получает конфигурацию Legal AI."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.legal_ai_url}/health")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=502, detail="Legal AI недоступен")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ошибка подключения: {str(e)}")
