"""Проксирование запросов в соседние сервисы."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request

from core.services import get_service_url

router = APIRouter()


def _resolve_service_url(service_key: Optional[str]) -> str:
    """Возвращает базовый URL сервиса или выбрасывает исключение."""
    if not service_key:
        raise HTTPException(status_code=400, detail="Service parameter is required")

    base_url = get_service_url(service_key)
    if base_url:
        return base_url

    raise HTTPException(status_code=400, detail=f"Unknown service: {service_key}")


@router.post("")
async def proxy_request(req: Request) -> Dict[str, Any]:
    """Перенаправляет запрос в указанный сервис и возвращает его ответ."""
    request_content_type = req.headers.get("content-type", "")
    
    if "application/json" not in request_content_type:
        raise HTTPException(status_code=400, detail="Unsupported content type")
    
    payload = await req.json()
    service_key: Optional[str] = payload.get("service")
    endpoint: Optional[str] = payload.get("endpoint")
    params: Optional[Dict[str, Any]] = payload.get("params")
    
    method_raw = payload.get("method", "GET")

    if not isinstance(method_raw, str):
        raise HTTPException(status_code=400, detail="Method must be a string")
    method = method_raw.upper()
    body = payload.get("body")
    proxy_content_type = payload.get("contentType")

    if endpoint is not None and not isinstance(endpoint, str):
        raise HTTPException(status_code=400, detail="Endpoint must be a string")

    if params is not None and not isinstance(params, dict):
        raise HTTPException(status_code=400, detail="Params must be an object")

    if proxy_content_type is not None and not isinstance(proxy_content_type, str):
        raise HTTPException(status_code=400, detail="contentType must be a string")

    base_url = _resolve_service_url(service_key)
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}" if endpoint else base_url.rstrip("/")

    async with httpx.AsyncClient(timeout=300) as client:
        try:
            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                request_kwargs: Dict[str, Any] = {}

                if params is not None:
                    request_kwargs["params"] = params

                if proxy_content_type == "text/plain":
                    if not isinstance(body, str):
                        raise HTTPException(status_code=400, detail="Body must be a string for text/plain requests")
                    request_kwargs["content"] = body
                    request_kwargs["headers"] = {"Content-Type": "text/plain"}
                else:                    
                    # По умолчанию отправляем JSON.
                    request_kwargs["json"] = body
                    if proxy_content_type:
                        request_kwargs.setdefault("headers", {})["Content-Type"] = proxy_content_type

                response = await client.post(url, **request_kwargs)
            else:
                raise HTTPException(status_code=405, detail="Метод не поддерживается")
        except httpx.RequestError as error:
            raise HTTPException(status_code=500, detail=f"Ошибка соединения: {error}") from error

    return {
        "status_code": response.status_code,
        "body": response.text,
        "headers": dict(response.headers),
        "url": str(response.url),
    }