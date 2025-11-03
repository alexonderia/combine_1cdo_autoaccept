"""Инструменты для работы с сервисами, доступными из админ-панели."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, MutableMapping, Optional

import httpx

from config import settings

DEFAULT_TIMEOUT = 5.0


@dataclass(frozen=True)
class ServiceDefinition:
    """Описание сервисов, доступных из админ-панели."""

    key: str
    name: str
    base_url: str

    def build_url(self, endpoint: Optional[str] = None) -> str:
        """Возвращает абсолютный URL с учётом указанного endpoint."""
        base = self.base_url.rstrip("/")
        if not endpoint:
            return base
        return f"{base}/{endpoint.lstrip('/')}"


@dataclass
class ServiceStatus:
    """Результат проверки состояния сервиса."""

    definition: ServiceDefinition
    status: str
    version: str
    details: Any = field(default_factory=dict)
    url: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        """Представление объекта в формате, ожидаемом клиентом API."""
        return {
            "name": self.definition.name,
            "key": self.definition.key,
            "url": self.url or self.definition.base_url,
            "status": self.status,
            "version": self.version,
            "details": self.details,
        }


SERVICE_REGISTRY: tuple[ServiceDefinition, ...] = (
    ServiceDefinition(
        key="contract-extractor",
        name="Contract Extractor",
        base_url=settings.contract_extractor_url,
    ),
    ServiceDefinition(
        key="globas-api",
        name="Globas API",
        base_url=settings.globas_api_url,
    ),
    ServiceDefinition(
        key="legal-ai",
        name="Legal AI",
        base_url=settings.legal_ai_url,
    ),
)

ADDITIONAL_SERVICE_URLS: Dict[str, str] = {
    "m-base": "http://localhost:8000/",
    "base": "http://localhost:8001/",
}

_SERVICE_MAP: MutableMapping[str, ServiceDefinition] = {
    service.key: service for service in SERVICE_REGISTRY
}


def get_service_by_key(key: str) -> Optional[ServiceDefinition]:
    """Возвращает описание сервиса по его ключу."""
    return _SERVICE_MAP.get(key)


def get_service_url(service_key: str) -> Optional[str]:
    """Возвращает URL сервиса по ключу с учётом дополнительного списка."""
    definition = get_service_by_key(service_key)
    if definition:
        return definition.base_url
    return ADDITIONAL_SERVICE_URLS.get(service_key)


async def fetch_service_health(
    service: ServiceDefinition,
    endpoint: str = "/health",
    timeout: float = DEFAULT_TIMEOUT,
) -> ServiceStatus:
    """Запрашивает состояние одного сервиса."""
    url = service.build_url(endpoint)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url)
        except httpx.RequestError as error:
            return ServiceStatus(
                definition=service,
                status="down",
                version="N/A",
                details={"error": str(error)},
                url=url,
            )

    if response.status_code == httpx.codes.OK:
        payload = response.json()
        version = str(payload.get("version", "N/A")) if isinstance(payload, dict) else "N/A"
        return ServiceStatus(
            definition=service,
            status="ok",
            version=version,
            details=payload,
            url=url,
        )

    return ServiceStatus(
        definition=service,
        status="error",
        version="N/A",
        details={"error": f"HTTP {response.status_code}"},
        url=url,
    )


async def fetch_all_services_health(
    services: Iterable[ServiceDefinition] = SERVICE_REGISTRY,
    endpoint: str = "/health",
    timeout: float = DEFAULT_TIMEOUT,
) -> List[ServiceStatus]:
    """Проверяет состояние всех указанных сервисов."""
    results: List[ServiceStatus] = []
    async with httpx.AsyncClient(timeout=timeout) as client:
        for service in services:
            url = service.build_url(endpoint)
            try:
                response = await client.get(url)
            except httpx.RequestError as error:
                results.append(
                    ServiceStatus(
                        definition=service,
                        status="down",
                        version="N/A",
                        details={"error": str(error)},
                        url=url,
                    )
                )
                continue

            if response.status_code == httpx.codes.OK:
                payload = response.json()
                version = (
                    str(payload.get("version", "N/A")) if isinstance(payload, dict) else "N/A"
                )
                results.append(
                    ServiceStatus(
                        definition=service,
                        status="ok",
                        version=version,
                        details=payload,
                        url=url,
                    )
                )
            else:
                results.append(
                    ServiceStatus(
                        definition=service,
                        status="error",
                        version="N/A",
                        details={"error": f"HTTP {response.status_code}"},
                        url=url,
                    )
                )
    return results


__all__ = [
    "ServiceDefinition",
    "ServiceStatus",
    "SERVICE_REGISTRY",
    "ADDITIONAL_SERVICE_URLS",
    "get_service_by_key",
    "get_service_url",
    "fetch_service_health",
    "fetch_all_services_health",
]
