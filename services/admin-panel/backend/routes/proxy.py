import json
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import httpx
from config import settings
from typing import Any

router = APIRouter()

class ProxyRequest(BaseModel):
    service: str   # 'contract-extractor' | 'legal-ai' | 'globas-api'
    method: str    # 'GET' | 'POST'
    endpoint: str  # например: '/api/status'
    body: dict | None = None


@router.post("")
async def proxy_request(req: Request):
    """Перенаправляет запрос в нужный сервис и возвращает ответ (код + тело)."""

    service_urls = {
        "contract-extractor": settings.contract_extractor_url,
        "legal-ai": settings.legal_ai_url,
        "globas-api": settings.globas_api_url,
        "m-base": "http://localhost:8000/",
        "base" : "http://localhost:8001/"
    }

    content_type = req.headers.get("content-type", "")

    # Для JSON
    if "application/json" in content_type:
        data = await req.json()
        service = data.get("service")
        method = data.get("method", "POST")
        endpoint = data.get("endpoint")
        body = data.get("body")

    # Для FormData / файлов
    elif "multipart/form-data" in content_type:
        form = await req.form()
        service = form.get("service")
        method = form.get("method", "POST")
        endpoint = form.get("endpoint")# Формируем dict с файлами для httpx
        files = {}
        for key, value in form.multi_items():
            if hasattr(value, "filename"):  # UploadFile
                files[key] = (value.filename, await value.read(), value.content_type)

        body = None  # body не нужен, используем files при POST

    else:
        raise HTTPException(status_code=400, detail="Unsupported content type")

    # data = await req.json() if "application/json" in req.headers.get("content-type", "") else None
    base_url = service_urls.get(service)
    if not base_url:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}" if endpoint else base_url

    # async with httpx.AsyncClient(timeout=20) as client:
    #     try:
    #         if req.method.upper() == "POST":
    #             if "multipart/form-data" in req.headers.get("content-type", ""):
    #                 # пересылаем FormData как есть
    #                 body_bytes = await req.body()
    #                 headers = {"Content-Type": req.headers["content-type"]}
    #                 response = await client.post(url, content=body_bytes, headers=headers)
    #             else:
    #                 # пересылаем JSON
    #                 response = await client.post(url, json=data.get("body") if data else {})
    #         elif req.method.upper() == "GET":
    #             response = await client.get(url, params=req.body)
    #         else:
    #             raise HTTPException(status_code=405, detail="Метод не поддерживается")

    #         # Возвращаем тело, код и заголовки
    #         return {
    #             "status_code": response.status_code,
    #             "body": response.text,
    #             "headers": dict(response.headers),
    #             "url": url,
    #         }

    #     except httpx.RequestError as e:
    #         raise HTTPException(status_code=500, detail=f"Ошибка соединения: {e}")

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            if method.upper() == "POST":
                if "multipart/form-data" in content_type:
                    response = await client.post(url, files=files)
                else:
                    response = await client.post(url, json=body)
            elif method.upper() == "GET":
                response = await client.get(url, params=body)
            else:
                raise HTTPException(status_code=405, detail="Метод не поддерживается")

            return {
                "status_code": response.status_code,
                "body": response.text,
                "headers": dict(response.headers),
                "url": str(response.url),
            }

        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка соединения: {e}")