"""Утилиты для чтения и обновления промптов."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass
class PromptFile:
    """Представление файла промпта."""

    name: str
    path: Path
    content: str

    def as_dict(self) -> dict:
        """Сериализованное представление файла для API."""
        return {"name": self.name, "content": self.content, "path": str(self.path)}


def _read_file(path: Path) -> str:
    """Читает файл, возвращая содержимое в виде строки."""
    return path.read_text(encoding="utf-8")


def list_prompts_for_service(base_dir: Path, prompt_files: Sequence[str]) -> List[PromptFile]:
    """Возвращает список промптов из набора заранее известных файлов."""
    prompts: List[PromptFile] = []
    for file_name in prompt_files:
        file_path = base_dir / file_name
        if not file_path.exists():
            continue
        try:
            content = _read_file(file_path)
        except OSError as error:
            content = f"Ошибка чтения: {error}"
        prompts.append(PromptFile(name=file_name, path=file_path, content=content))
    return prompts


def list_prompts_from_directory(base_dir: Path, pattern: str) -> Iterable[PromptFile]:
    """Перечисляет промпты по шаблону внутри каталога."""
    for file_path in base_dir.glob(pattern):
        try:
            content = _read_file(file_path)
        except OSError as error:
            content = f"Ошибка чтения: {error}"
        relative = file_path.relative_to(base_dir.parent)
        yield PromptFile(name=str(relative), path=file_path, content=content)


def read_prompt_file(path: Path) -> str:
    """Возвращает содержимое указанного файла промпта."""
    if not path.exists():
        raise FileNotFoundError(str(path))
    return _read_file(path)


__all__ = [
    "PromptFile",
    "list_prompts_for_service",
    "list_prompts_from_directory",
    "read_prompt_file",
]
