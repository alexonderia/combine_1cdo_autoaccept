from __future__ import annotations

import json
from typing import Iterable

from fastapi import HTTPException, UploadFile

from app.core.logger import get_logger

logger = get_logger(__name__)


def _decode_bytes(content: bytes, encodings: Iterable[str]) -> str:
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return content.decode(encoding)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.debug("Failed to decode upload with %s: %s", encoding, exc)
    if last_error is not None:
        raise last_error
    return content.decode()


async def read_text_from_upload(file: UploadFile) -> str:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Загруженный файл пуст")
    try:
        return _decode_bytes(content, ("utf-8-sig", "utf-8", "cp1251"))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to decode uploaded file")
        raise HTTPException(
            status_code=400,
            detail="Не удалось определить кодировку файла. Поддерживаются UTF-8 и CP1251.",
        ) from exc


async def read_json_from_upload(file: UploadFile):
    text = await read_text_from_upload(file)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.exception("Failed to parse uploaded JSON")
        raise HTTPException(status_code=400, detail="Файл с эталоном содержит некорректный JSON") from exc
