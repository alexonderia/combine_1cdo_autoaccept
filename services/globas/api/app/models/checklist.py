"""Модели ответов API и структуры чек-листа для сервиса Globas."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RiskScores(BaseModel):
    """Скоринговые показатели компании."""

    grade: Optional[str] = None
    solvency: Optional[int] = None
    reliability: Optional[int] = None
    compliance_flag: Optional[str] = None


class ChecklistAnswer(BaseModel):
    """Нормализованный ответ на пункт чек-листа."""

    code: str
    text: str
    status: str
    raw_value: Optional[Any] = None


class ChecklistDetail(BaseModel):
    """Детализация конкретного пункта чек-листа."""

    code: str
    label: str
    answer: ChecklistAnswer


class ChecklistItem(BaseModel):
    """Пункт чек-листа с вопросом и ответом."""

    code: str
    question: str
    answer: ChecklistAnswer
    data: Optional[Dict[str, Any]] = None
    details: Optional[List[ChecklistDetail]] = None


class ChecklistMetadata(BaseModel):
    """Метаданные сформированного документа."""

    title: str
    checked_at: Optional[str] = None
    checked_by: Optional[str] = None
    digital_signature: Optional[str] = None
    locale: str
    field_labels: Dict[str, str] = Field(default_factory=dict)


class ChecklistCompany(BaseModel):
    """Краткая информация о компании, для которой формируется отчёт."""

    id: UUID
    name: str
    inn: str
    ogrn: str
    status: str
    okved_main: str
    reg_date: Optional[date] = None
    address: str
    risk_scores: RiskScores = Field(default_factory=RiskScores)


class ChecklistDocument(BaseModel):
    """Готовый документ чек-листа, включающий пункты и метаданные."""

    company: ChecklistCompany
    items: List[ChecklistItem]
    metadata: ChecklistMetadata


class ChecklistResponse(BaseModel):
    """Ответ API на запрос формирования чек-листа."""

    checklist_document: ChecklistDocument


class CompanyOut(BaseModel):
    """Базовое описание компании для административных эндпоинтов."""

    id: UUID
    name: str
    inn: str
    ogrn: str
    status: str
    okved_main: str
    reg_date: Optional[date] = None
    address: str
    grade: Optional[str] = None
    solvency: Optional[int] = None
    reliability: Optional[int] = None
    compliance_flag: Optional[str] = None
    checklist_document: Optional[ChecklistDocument] = None
