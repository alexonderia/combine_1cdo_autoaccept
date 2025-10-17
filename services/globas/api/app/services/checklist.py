"""Утилиты формирования чек-листа должной осмотрительности."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional

from ..localization import CHECKLIST_TEXTS
from ..models.checklist import (
    ChecklistAnswer,
    ChecklistDetail,
    ChecklistDocument,
    ChecklistItem,
    ChecklistMetadata,
    ChecklistCompany,
    RiskScores,
)


def _to_float(value: Any) -> Any:
    """Преобразует Decimal в float для сериализации."""

    if isinstance(value, Decimal):
        return float(value)
    return value


def to_float(value: Any) -> Any:
    """Публичная обёртка для приведения Decimal к float."""

    return _to_float(value)


def _to_int(value: Any) -> Any:
    """Преобразует Decimal в int для удобства потребителей."""

    if isinstance(value, Decimal):
        return int(value)
    return value


_ANSWERS = CHECKLIST_TEXTS.get("answers", {})
_QUESTIONS = CHECKLIST_TEXTS.get("questions", {})
_METADATA_CFG = CHECKLIST_TEXTS.get("metadata", {})
_EXPOSURE_LABELS = CHECKLIST_TEXTS.get("exposure_labels", {})
_LOCALE = CHECKLIST_TEXTS.get("locale", "ru-RU")


def _answer_text(key: str, fallback: str) -> str:
    """Возвращает локализованный текст ответа."""

    return _ANSWERS.get(key, fallback)


_MISSING_TEXT = _answer_text("missing", "Нет данных")
_BOOL_YES = _answer_text("bool_yes", "Да")
_BOOL_NO = _answer_text("bool_no", "Нет")
_AVAILABLE_YES = _answer_text("available_yes", "Имеется")
_AVAILABLE_NO = _answer_text("available_no", "Не имеется")
_COLLECTION_YES = _answer_text("collection_yes", "Имеются")
_COLLECTION_NO = _answer_text("collection_no", "Не имеются")
_EXISTS_YES = _answer_text("exists_yes", "Есть")
_EXISTS_NO = _answer_text("exists_no", "Нет")
_INSPECTION_FOUND = _answer_text("inspection_found_yes", "Выявляли")
_INSPECTION_NOT_FOUND = _answer_text("inspection_found_no", "Не выявляли")


def _question_text(code: str) -> str:
    """Возвращает локализованный текст вопроса по коду."""

    return _QUESTIONS.get(code, code.replace("_", " ").capitalize())


def _answer_missing(raw_value: Any = None) -> ChecklistAnswer:
    """Формирует ответ об отсутствии данных."""

    return ChecklistAnswer(code="missing", text=_MISSING_TEXT, status="unknown", raw_value=raw_value)


def _positive_answer(
    value: Optional[bool],
    *,
    yes_key: str = "bool_yes",
    no_key: str = "bool_no",
    fallback_yes: Optional[str] = None,
    fallback_no: Optional[str] = None,
    raw_value: Any = None,
    status_when_true: str = "ok",
    status_when_false: str = "issue",
) -> ChecklistAnswer:
    """Формирует положительный ответ с учётом локализации."""

    if value is None:
        return _answer_missing(raw_value)
    yes_default = fallback_yes if fallback_yes is not None else _BOOL_YES
    no_default = fallback_no if fallback_no is not None else _BOOL_NO
    code = yes_key if value else no_key
    text = _answer_text(code, yes_default if value else no_default)
    status = status_when_true if value else status_when_false
    stored_raw = value if raw_value is None else raw_value
    return ChecklistAnswer(code=code, text=text, status=status, raw_value=stored_raw)


def _negated_issue_answer(value: Optional[bool], *, raw_value: Any = None) -> ChecklistAnswer:
    """Инвертирует ответ и статус, когда наличие проблемы считается негативом."""

    if value is None:
        return _answer_missing(raw_value)
    has_issue = bool(value)
    code = "bool_no" if not has_issue else "bool_yes"
    text = _answer_text(code, _BOOL_NO if not has_issue else _BOOL_YES)
    status = "ok" if not has_issue else "issue"
    stored_raw = value if raw_value is None else raw_value
    return ChecklistAnswer(code=code, text=text, status=status, raw_value=stored_raw)


def _availability_from_count(count: Optional[int]) -> ChecklistAnswer:
    """Возвращает ответ на основании количества найденных сущностей."""

    if count is None:
        return _answer_missing(count)
    has_items = count > 0
    code = "available_yes" if has_items else "available_no"
    text = _answer_text(code, _AVAILABLE_YES if has_items else _AVAILABLE_NO)
    status = "ok" if has_items else "issue"
    return ChecklistAnswer(code=code, text=text, status=status, raw_value=count)


def _exposure_detail_answer(value: Optional[bool]) -> ChecklistAnswer:
    """Строит ответ для отдельных факторов риска."""

    if value is None:
        return _answer_missing(value)
    code = "exists_yes" if value else "exists_no"
    text = _answer_text(code, _EXISTS_YES if value else _EXISTS_NO)
    status = "issue" if value else "ok"
    return ChecklistAnswer(code=code, text=text, status=status, raw_value=value)


def _inspection_answer(flag: Optional[bool]) -> ChecklistAnswer:
    """Формирует ответ для блоков о проверках и инспекциях."""

    if flag is None:
        return _answer_missing(flag)
    code = "inspection_found_yes" if flag else "inspection_found_no"
    text = _INSPECTION_FOUND if flag else _INSPECTION_NOT_FOUND
    status = "issue" if flag else "ok"
    return ChecklistAnswer(code=code, text=text, status=status, raw_value=flag)


def build_checklist_document(
    company: Mapping[str, Any],
    due_diligence: Optional[Mapping[str, Any]],
) -> ChecklistDocument:
    """Формирует структуру чек-листа на основе данных компании."""

    reg_date_value = company.get("reg_date")
    if isinstance(reg_date_value, date):
        reg_date_obj = reg_date_value
    elif isinstance(reg_date_value, str) and reg_date_value:
        try:
            reg_date_obj = date.fromisoformat(reg_date_value)
        except ValueError:
            reg_date_obj = None
    else:
        reg_date_obj = None

    risk_scores = RiskScores(
        grade=company.get("grade"),
        solvency=_to_int(company.get("solvency")),
        reliability=_to_int(company.get("reliability")),
        compliance_flag=company.get("compliance_flag"),
    )

    company_model = ChecklistCompany(
        id=company.get("id"),
        name=company.get("name"),
        inn=company.get("inn"),
        ogrn=company.get("ogrn"),
        status=company.get("status"),
        okved_main=company.get("okved_main"),
        reg_date=reg_date_obj,
        address=company.get("address"),
        risk_scores=risk_scores,
    )

    dd_map = dict(due_diligence) if due_diligence else {}

    age_years = dd_map.get("age_years")
    age_bool = None if age_years is None else age_years >= 3

    staff_count = dd_map.get("staff_count")
    quality_details = dd_map.get("quality_docs_details") or ""
    quality_documents = [item.strip() for item in quality_details.split(",") if item.strip()]
    assets_total_value = _to_float(dd_map.get("assets_total_value")) if dd_map else None

    exposures = {
        "tax_debt": dd_map.get("tax_debt"),
        "fssp_debt": dd_map.get("fssp_debt"),
        "open_credit_lines": dd_map.get("open_credit_lines"),
        "leasing": dd_map.get("has_leasing"),
    }
    known_exposures = [value for value in exposures.values() if value is not None]
    any_issue = any(bool(value) for value in known_exposures)
    exposures_answer = _negated_issue_answer(any_issue if known_exposures else None)
    exposure_details = [
        ChecklistDetail(
            code=key,
            label=_EXPOSURE_LABELS.get(key, key),
            answer=_exposure_detail_answer(value),
        )
        for key, value in exposures.items()
    ]

    gov_count = dd_map.get("gov_contracts_count")
    gov_total = _to_float(dd_map.get("gov_contracts_total")) if dd_map else None

    blocked_banks_raw = dd_map.get("blocked_banks") or ""
    blocked_banks = [bank.strip() for bank in blocked_banks_raw.split(",") if bank.strip()]
    regulatory_details = dd_map.get("regulatory_violations_details") or ""
    regulatory_list = [item.strip() for item in regulatory_details.split(";") if item.strip()]
    regulatory_flag = dd_map.get("regulatory_violations")

    items: List[ChecklistItem] = [
        ChecklistItem(
            code="egrul_invalid_data",
            question=_question_text("egrul_invalid_data"),
            answer=_negated_issue_answer(dd_map.get("egrul_has_invalid_data")),
        ),
        ChecklistItem(
            code="liquidation_bankruptcy",
            question=_question_text("liquidation_bankruptcy"),
            answer=_negated_issue_answer(dd_map.get("status_issue")),
        ),
        ChecklistItem(
            code="identity_matches",
            question=_question_text("identity_matches"),
            answer=_positive_answer(dd_map.get("identity_matches")),
        ),
        ChecklistItem(
            code="company_age_requirement",
            question=_question_text("company_age_requirement"),
            answer=_positive_answer(age_bool, raw_value=age_bool),
            data={"age_years": age_years} if age_years is not None else None,
        ),
        ChecklistItem(
            code="staff_sufficiency",
            question=_question_text("staff_sufficiency"),
            answer=_positive_answer(dd_map.get("staff_sufficient")),
            data={"staff_count": staff_count} if staff_count is not None else None,
        ),
        ChecklistItem(
            code="quality_docs",
            question=_question_text("quality_docs"),
            answer=_positive_answer(
                dd_map.get("has_quality_docs"),
                yes_key="collection_yes",
                no_key="collection_no",
                fallback_yes=_COLLECTION_YES,
                fallback_no=_COLLECTION_NO,
            ),
            data={"documents": quality_documents} if quality_documents else None,
        ),
        ChecklistItem(
            code="has_assets",
            question=_question_text("has_assets"),
            answer=_positive_answer(dd_map.get("has_assets")),
            data={"assets_total_value": assets_total_value} if assets_total_value is not None else None,
        ),
        ChecklistItem(
            code="tax_debt_and_obligations",
            question=_question_text("tax_debt_and_obligations"),
            answer=exposures_answer,
            details=exposure_details,
        ),
        ChecklistItem(
            code="active_court_cases",
            question=_question_text("active_court_cases"),
            answer=_negated_issue_answer(dd_map.get("active_court_cases")),
        ),
        ChecklistItem(
            code="executive_debt",
            question=_question_text("executive_debt"),
            answer=_negated_issue_answer(dd_map.get("executive_debt")),
        ),
        ChecklistItem(
            code="gov_contracts_experience",
            question=_question_text("gov_contracts_experience"),
            answer=_availability_from_count(gov_count),
            data={
                "count": gov_count,
                "total_amount": gov_total,
            }
            if gov_count is not None or gov_total is not None
            else None,
        ),
        ChecklistItem(
            code="in_rnp",
            question=_question_text("in_rnp"),
            answer=_negated_issue_answer(dd_map.get("in_rnp")),
        ),
        ChecklistItem(
            code="mass_registration",
            question=_question_text("mass_registration"),
            answer=_negated_issue_answer(dd_map.get("mass_registration")),
        ),
        ChecklistItem(
            code="director_disqualified",
            question=_question_text("director_disqualified"),
            answer=_negated_issue_answer(dd_map.get("director_disqualified")),
        ),
        ChecklistItem(
            code="director_nominee",
            question=_question_text("director_nominee"),
            answer=_negated_issue_answer(dd_map.get("director_nominee")),
        ),
        ChecklistItem(
            code="power_of_attorney",
            question=_question_text("power_of_attorney"),
            answer=_positive_answer(
                dd_map.get("has_power_of_attorney"),
                yes_key="collection_yes",
                no_key="collection_no",
                fallback_yes=_COLLECTION_YES,
                fallback_no=_COLLECTION_NO,
            ),
        ),
        ChecklistItem(
            code="blocked_accounts",
            question=_question_text("blocked_accounts"),
            answer=_positive_answer(
                dd_map.get("blocked_accounts"),
                raw_value=dd_map.get("blocked_accounts"),
                status_when_true="issue",
                status_when_false="ok",
            ),
            data={"banks": blocked_banks} if blocked_banks else None,
        ),
        ChecklistItem(
            code="tax_clearance_certificate",
            question=_question_text("tax_clearance_certificate"),
            answer=_positive_answer(
                dd_map.get("tax_clearance_recent"),
                yes_key="available_yes",
                no_key="available_no",
                fallback_yes=_AVAILABLE_YES,
                fallback_no=_AVAILABLE_NO,
            ),
        ),
        ChecklistItem(
            code="regulatory_violations",
            question=_question_text("regulatory_violations"),
            answer=_inspection_answer(regulatory_flag),
            data={"details": regulatory_details, "violations": regulatory_list}
            if regulatory_details
            else None,
        ),
    ]

    metadata_fields = _METADATA_CFG.get("fields", {})
    metadata = ChecklistMetadata(
        title=_METADATA_CFG.get(
            "title",
            "Чек-лист к памятке о порядке проведения должной осмотрительности",
        ),
        checked_at=date.today().isoformat(),
        checked_by=None,
        digital_signature=None,
        locale=_LOCALE,
        field_labels=metadata_fields,
    )

    return ChecklistDocument(company=company_model, items=items, metadata=metadata)
