"""Маршруты, связанные с обработкой и проверкой текстов контрактов."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

from ...application import AppContainer
from ...dependencies import container_dependency
from ...services.compare import compare_dicts
from ...services.utils import read_json_from_upload, read_text_from_upload
from ...services.warnings import to_payload

router = APIRouter(tags=["extraction"])


async def _process_text_payload(text: str, container: AppContainer) -> Any:
    """Запускает конвейер извлечения и возвращает стандартный ответ."""

    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty text")

    try:
        data, warns, errors, debug, ext_prompt = await container.pipeline.run(text)
    except Exception as exc:  # pragma: no cover - защитная обработка
        raise HTTPException(status_code=500, detail="Internal processing error") from exc

    response_content: Dict[str, Any] = {
        "ext_prompt": ext_prompt or "",
        "data": data,
        "warnings": to_payload(warns),
        "debug": debug,
    }

    if errors:
        response_content.update({"ok": False, "validation_errors": errors})
        return JSONResponse(status_code=422, content=response_content)  # type: ignore[return-value]

    response_content["ok"] = True
    return response_content


@router.post("/check")
async def check(
    file: UploadFile = File(None),
    payload: Optional[Dict[str, Any]] = Body(None),
    container: AppContainer = Depends(container_dependency),
):
    """Принимает текст контракта и возвращает извлечённые данные."""

    if file is None and not payload:
        raise HTTPException(
            status_code=400,
            detail="Provide a text file or JSON body with {'text': '...'}",
        )

    if file is not None:
        text = await read_text_from_upload(file)
    else:
        text = payload.get("text", "") if isinstance(payload, dict) else ""

    result = await _process_text_payload(text, container)
    return result


@router.post("/txtcheck")
async def txtcheck(
    text: str = Body(..., media_type="text/plain"),
    container: AppContainer = Depends(container_dependency),
):
    """Принимает чистый текст в теле запроса."""

    result = await _process_text_payload(text, container)
    return result


@router.post("/rawcheck")
async def rawcheck(
    file: UploadFile = File(None),
    payload: Optional[Dict[str, Any]] = Body(None),
    container: AppContainer = Depends(container_dependency),
):
    """Возвращает сырые ответы LLM для целей отладки."""

    if file is None and not payload:
        raise HTTPException(
            status_code=400,
            detail="Provide a text file or JSON body with {'text': '...'}",
        )

    if file is not None:
        text = await read_text_from_upload(file)
    else:
        text = payload.get("text", "") if isinstance(payload, dict) else ""

    await _process_text_payload(text, container)  # валидация текста и возможные ошибки

    _, _, _, debug, _ = await container.pipeline.run(text)
    raw_outputs = []
    if isinstance(debug, dict):
        raw_outputs = debug.get("llm_raw_outputs") or []

    if not raw_outputs:
        return PlainTextResponse("", status_code=200)

    body = "\n\n-----\n\n".join(raw_outputs)
    return PlainTextResponse(body, status_code=200)


@router.post("/test")
async def test(
    text_file: UploadFile = File(...),
    gold_json: UploadFile = File(...),
    container: AppContainer = Depends(container_dependency),
):
    """Сравнивает результат извлечения с эталонными данными."""

    text = await read_text_from_upload(text_file)
    gold = await read_json_from_upload(gold_json)

    data, warns, errors, debug, ext_prompt = await container.pipeline.run(text)
    rows, summary = compare_dicts(gold, data)

    return {
        "ext_prompt": ext_prompt or "",
        "ok": True,
        "table": rows,
        "summary": summary,
        "warnings": to_payload(warns),
        **({"validation_errors": errors} if errors else {}),
        "debug": debug,
    }
