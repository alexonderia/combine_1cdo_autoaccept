#!/usr/bin/env python3
"""Скрипт запуска локальной админ-панели."""

import uvicorn
from config import settings

if __name__ == "__main__":
    print(f"Запуск админ-панели на порту {settings.port}")
    print(f"URL: http://localhost:{settings.port}")
    print(f"API документация: http://localhost:{settings.port}/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
