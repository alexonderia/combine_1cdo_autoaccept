"""Вспомогательные компоненты приложения FastAPI для админ-панели."""

from .services import (
    ServiceDefinition,
    ServiceStatus,
    SERVICE_REGISTRY,
    ADDITIONAL_SERVICE_URLS,
    get_service_by_key,
    get_service_url,
    fetch_service_health,
    fetch_all_services_health,
)
from .prompts import PromptFile, list_prompts_for_service, read_prompt_file

__all__ = [
    "ServiceDefinition",
    "ServiceStatus",
    "SERVICE_REGISTRY",
    "ADDITIONAL_SERVICE_URLS",
    "get_service_by_key",
    "get_service_url",
    "fetch_service_health",
    "fetch_all_services_health",
    "PromptFile",
    "list_prompts_for_service",
    "read_prompt_file",
]
