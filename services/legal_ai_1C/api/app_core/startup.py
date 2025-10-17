from __future__ import annotations

import asyncio
import httpx
from fastapi import FastAPI

from .config import settings
from .logger import get_logger

try:  # pragma: no cover
    import torch  # type: ignore
except Exception:  # noqa: S110
    torch = None

logger = get_logger(__name__)

def register_startup(app: FastAPI):
    @app.on_event("startup")
    async def startup_checks():
        if not settings.STARTUP_CHECKS:
            logger.info("Startup checks skipped by env")
            return
        logger.info("Startup checks begin", extra={"mode": "light"})

        # Ollama
        ok_ollama = False
        for _ in range(settings.SELF_CHECK_TIMEOUT):
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    r = await client.get(f"{settings.OLLAMA_URL}/api/tags")
                    if r.status_code == 200:
                        ok_ollama = True
                        models = [m["name"] for m in r.json().get("models", [])]
                        logger.info(
                            "Ollama available",
                            extra={
                                "models_preview": models[:3],
                                "models_truncated": len(models) > 3,
                            },
                        )
                        break
            except Exception:  # noqa: BLE001
                logger.debug("Ollama probe failed", exc_info=True)
            await asyncio.sleep(1)
        if not ok_ollama:
            logger.warning("Ollama not reachable", extra={"url": settings.OLLAMA_URL})

        # Qdrant
        ok_qdrant = False
        for _ in range(settings.SELF_CHECK_TIMEOUT):
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    r = await client.get(f"{settings.QDRANT_URL}/collections")
                    if r.status_code == 200:
                        ok_qdrant = True
                        names = [c["name"] for c in r.json().get("collections", [])]
                        logger.info(
                            "Qdrant available",
                            extra={"collections": names},
                        )
                        break
            except Exception:  # noqa: BLE001
                logger.debug("Qdrant probe failed", exc_info=True)
            await asyncio.sleep(1)
        if not ok_qdrant:
            logger.warning("Qdrant not reachable", extra={"url": settings.QDRANT_URL})

        # Torch/CUDA (без инициализации девайса)
        if torch is not None:
            try:
                logger.info(
                    "Torch info",
                    extra={
                        "torch_version": torch.__version__,
                        "cuda_available": torch.cuda.is_available(),
                        "cuda_version": getattr(torch.version, "cuda", None),
                    },
                )
                if settings.STARTUP_CUDA_NAME and torch.cuda.is_available():
                    name = torch.cuda.get_device_name(0)
                    logger.info("CUDA device detected", extra={"device": name})
            except Exception:  # noqa: BLE001
                logger.exception("Torch info error")
        else:
            logger.info("Torch not installed; skipping CUDA probe")

        # Тест-генерация (по флагу)
        if ok_ollama and settings.SELF_CHECK_GEN:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    payload = {"model": settings.OLLAMA_MODEL, "prompt": "ping", "stream": False, "options": {"num_predict": 4}}
                    r = await client.post(f"{settings.OLLAMA_URL}/api/generate", json=payload)
                    status = "OK" if r.status_code == 200 else f"FAIL {r.status_code}"
                    logger.info("Ollama test generate", extra={"status": status})
            except Exception:  # noqa: BLE001
                logger.exception("Ollama test generate error")

        logger.info("Startup checks end")
