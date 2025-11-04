"""Точка входа FastAPI-приложения админ-панели."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from routes import config, health, prompts, proxy, services

app = FastAPI(
    title=settings.app_name,
    description="Веб-оболочка для администрирования сервисов (локальная версия)",
    version=settings.version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(proxy.router, prefix="/api/proxy", tags=["proxy"])


frontend_dir = Path(__file__).parent / "static"
index_file = frontend_dir / "index.html"

if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    @app.get("/", response_class=HTMLResponse)
    async def serve_index() -> FileResponse:
        """Возвращает главную страницу фронтенда."""
        return FileResponse(index_file)
else:

    @app.get("/", response_class=HTMLResponse)
    async def frontend_not_built() -> HTMLResponse:
        """Сообщает о том, что фронтенд не собран."""
        return HTMLResponse(
            """
            <h2>Frontend не собран</h2>
            <p>Собери React-приложение:</p>
            <pre>cd ../frontend && npm install && npm run build</pre>
            """
        )
