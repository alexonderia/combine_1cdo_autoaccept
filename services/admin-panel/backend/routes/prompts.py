"""Маршруты для чтения и обновления промптов сервисов."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.prompts import (
    PromptFile,
    list_prompts_for_service,
    list_prompts_from_directory,
    read_prompt_file,
)

router = APIRouter()

PROMPTS_ROOT = Path(__file__).resolve().parent.parent / "prompts"
CONTRACT_PROMPTS_DIR = PROMPTS_ROOT / "contract-extractor"
LEGAL_AI_PROMPTS_DIR = PROMPTS_ROOT / "legal-ai"

CONTRACT_PROMPT_FILES = (
    "system.txt",
    "user_template.txt",
    "summary_system.txt",
    "summary_user_template.txt",
    "field_guidelines.md",
)

LEGAL_AI_PROMPT_FILES = (
    "analyze_system.txt",
    "analyze_user.txt",
    "business_system.txt",
    "business_user.txt",
    "overview_system.txt",
    "overview_user.txt",
    "analyze_system_lenient_rule.txt",
)

PROMPT_DIRECTORIES: Dict[str, Path] = {
    "Contract Extractor": CONTRACT_PROMPTS_DIR,
    "Legal AI": LEGAL_AI_PROMPTS_DIR,
}


class PromptUpdateRequest(BaseModel):
    """Модель запроса для обновления промпта."""

    service: str
    name: str
    content: str


def _serialize(prompts: List[PromptFile]) -> List[Dict[str, Any]]:
    """Преобразует список промптов в формат API."""
    return [prompt.as_dict() for prompt in prompts]


def _resolve_prompt_path(directory: Path, name: str) -> Path:
    """Возвращает абсолютный путь к файлу промпта внутри директории сервиса."""
    base = directory.resolve()
    candidate = (base / name).resolve()
    if not candidate.is_relative_to(base):
        raise HTTPException(status_code=400, detail="Некорректный путь к файлу")
    return candidate


@router.get("/list")
async def list_prompts() -> List[Dict[str, Any]]:
    """Возвращает список всех промптов по сервисам."""
    services: List[Dict[str, Any]] = []

    if CONTRACT_PROMPTS_DIR.exists():
        prompts: List[PromptFile] = []
        prompts.extend(list_prompts_for_service(CONTRACT_PROMPTS_DIR, CONTRACT_PROMPT_FILES))

        fields_dir = CONTRACT_PROMPTS_DIR / "fields"
        if fields_dir.exists():
            prompts.extend(list(list_prompts_from_directory(fields_dir, "*.md")))

        services.append({"name": "Contract Extractor", "prompts": _serialize(prompts)})

    if LEGAL_AI_PROMPTS_DIR.exists():
        prompts = list_prompts_for_service(LEGAL_AI_PROMPTS_DIR, LEGAL_AI_PROMPT_FILES)
        services.append({"name": "Legal AI", "prompts": _serialize(prompts)})

    return services


@router.post("/update")
async def update_prompt(request: PromptUpdateRequest) -> Dict[str, str]:
    """Обновляет содержимое промпта."""
    directory = PROMPT_DIRECTORIES.get(request.service)
    if not directory:
        raise HTTPException(status_code=400, detail="Неизвестный сервис")

    file_path = _resolve_prompt_path(directory, request.name)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    try:
        file_path.write_text(request.content, encoding="utf-8")
    except OSError as error:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении промпта: {error}") from error

    return {"status": "success", "message": "Промпт успешно обновлен"}


@router.get("/contract-extractor/{prompt_name}")
async def get_contract_extractor_prompt(prompt_name: str) -> Dict[str, str]:
    """Получает содержимое конкретного промпта Contract Extractor."""
    file_path = _resolve_prompt_path(CONTRACT_PROMPTS_DIR, prompt_name)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    try:
        content = read_prompt_file(file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Файл не найден") from None
    return {"content": content}


@router.get("/legal-ai/{prompt_name}")
async def get_legal_ai_prompt(prompt_name: str) -> Dict[str, str]:
    """Получает содержимое конкретного промпта Legal AI."""
    file_path = _resolve_prompt_path(LEGAL_AI_PROMPTS_DIR, prompt_name)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    try:
        content = read_prompt_file(file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Файл не найден") from None
    return {"content": content}
