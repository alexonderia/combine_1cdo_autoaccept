import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from routes import health, services, prompts, config, proxy
from config import Settings

app = FastAPI(
    title="Admin Panel (Local)",
    description="Веб-оболочка для администрирования сервисов (локальная версия)",
    version="1.0.0",
)

# Разрешаем CORS для локальной разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роуты API
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(proxy.router, prefix="/api/proxy", tags=["proxy"])


# ===== STATIC / FRONTEND =====
frontend_dir = os.path.join(os.path.dirname(__file__), "static")
index_file = os.path.join(frontend_dir, "index.html")

if os.path.exists(frontend_dir):
    # Раздаём все файлы из папки сборки React
    app.mount(
        "/",
        StaticFiles(directory=frontend_dir, html=True),
        name="frontend",
    )

    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        """Главная страница фронтенда."""
        return FileResponse(index_file)

else:
    @app.get("/", response_class=HTMLResponse)
    async def frontend_not_built():
        return HTMLResponse("""
        <h2>Frontend не собран</h2>
        <p>Собери React-приложение:</p>
        <pre>cd ../frontend && npm install && npm run build</pre>
        """)
