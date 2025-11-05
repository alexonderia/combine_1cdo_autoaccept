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
    content_type = req.headers.get("content-type", "")
    service_key: Optional[str] = None
    method = "POST"
    endpoint: Optional[str] = None
    body: Optional[Dict[str, Any]] = None
    files: Optional[Dict[str, Any]] = None

    if "application/json" in content_type:
        payload = await req.json()
        service_key = payload.get("service")
        method = payload.get("method", "POST")
        endpoint = payload.get("endpoint")
        body = payload.get("body")
    elif "multipart/form-data" in content_type:
        form = await req.form()
        service_key = form.get("service")
        method = form.get("method", "POST")
        endpoint = form.get("endpoint")
        files = {}
        body = {}
        for key, value in form.multi_items():
            if key in {"service", "method", "endpoint"}:
                continue
            if hasattr(value, "filename"):
                files[key] = (value.filename, await value.read(), value.content_type)
            else:
                body[key] = value
    else:
        raise HTTPException(status_code=400, detail="Unsupported content type")

    base_url = _resolve_service_url(service_key)
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}" if endpoint else base_url.rstrip("/")

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            if method.upper() == "POST":
                if files:
                    response = await client.post(url, data=body or {}, files=files)
                    request_kwargs: Dict[str, Any] = {"files": files}
                    if body:
                        request_kwargs["data"] = body
                    response = await client.post(url, **request_kwargs)
                else:
                    response = await client.post(url, json=body)
            elif method.upper() == "GET":
                response = await client.get(url, params=body)
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
