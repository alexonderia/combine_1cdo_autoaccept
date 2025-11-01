"""Конфигурация админ-панели для локального запуска."""

from pydantic import BaseModel
from typing import Dict, Any
import os

class Settings(BaseModel):
    # URLs сервисов для локального запуска
    # contract_extractor_url: str = "http://localhost:18080"
    # globas_api_url: str = "http://localhost:18090"
    # legal_ai_url: str = "http://localhost:18100"

    # URLs сервисов для запуска через Docker
    contract_extractor_url: str = "http://contract-extractor:8080"
    globas_api_url: str = "http://globas-api:8000"
    legal_ai_url: str = "http://legal-ai:8000"
    
    # SERVICES_URL: http://proxy:8000        # если идём через Nginx
    # CONTRACT_EXTRACTOR_URL: http://contract-extractor:8080
    # GLOBAS_API_URL: http://globas-api:8000
    # LEGAL_AI_URL: http://legal-ai:8000
    # # Пути к промптам для локального запуска
    # contract_extractor_prompts_path: str = "./prompts/contract-extractor"
    # legal_ai_prompts_path: str = "./prompts/legal-ai"
    
    # Настройки приложения
    app_name: str = "Admin Panel (Local)"
    version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Порт для локального запуска
    port: int = int(os.getenv("PORT", "8001"))

settings = Settings()
