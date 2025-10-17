from __future__ import annotations

from datetime import date
from uuid import UUID

from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Literal

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

import yaml
import pandas as pd
from io import StringIO

from .db import engine, ensure_schema
from .generator_core import generate_dataset
from .loader import init_schema, load_to_db
from .localization import CHECKLIST_TEXTS

app = FastAPI(
    title="Synthetic Globas API",
    version="0.1.0",
    description="API для генерации и проверки синтетических данных о контрагентах",
)


class RiskScores(BaseModel):
    grade: Optional[str] = None
    solvency: Optional[int] = None
    reliability: Optional[int] = None
    compliance_flag: Optional[str] = None


class ChecklistAnswer(BaseModel):
    code: str
    text: str
    status: Literal["ok", "issue", "unknown"]
    raw_value: Optional[Any] = None


class ChecklistDetail(BaseModel):
    code: str
    label: str
    answer: ChecklistAnswer


class ChecklistItem(BaseModel):
    code: str
    question: str
    answer: ChecklistAnswer
    data: Optional[Dict[str, Any]] = None
    details: Optional[List[ChecklistDetail]] = None


class ChecklistMetadata(BaseModel):
    title: str
    checked_at: Optional[str] = None
    checked_by: Optional[str] = None
    digital_signature: Optional[str] = None
    locale: str
    field_labels: Dict[str, str] = Field(default_factory=dict)


class ChecklistCompany(BaseModel):
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
    company: ChecklistCompany
    items: List[ChecklistItem]
    metadata: ChecklistMetadata


class ChecklistResponse(BaseModel):
    checklist_document: ChecklistDocument


class CompanyOut(BaseModel):
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


def _to_float(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def _to_int(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value)
    return value


_ANSWERS = CHECKLIST_TEXTS.get("answers", {})
_QUESTIONS = CHECKLIST_TEXTS.get("questions", {})
_METADATA_CFG = CHECKLIST_TEXTS.get("metadata", {})
_EXPOSURE_LABELS = CHECKLIST_TEXTS.get("exposure_labels", {})
_LOCALE = CHECKLIST_TEXTS.get("locale", "ru-RU")


def _answer_text(key: str, fallback: str) -> str:
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
    return _QUESTIONS.get(code, code.replace("_", " ").capitalize())


def _answer_missing(raw_value: Any = None) -> ChecklistAnswer:
    return ChecklistAnswer(code="missing", text=_MISSING_TEXT, status="unknown", raw_value=raw_value)


def _positive_answer(
    value: Optional[bool],
    *,
    yes_key: str = "bool_yes",
    no_key: str = "bool_no",
    fallback_yes: Optional[str] = None,
    fallback_no: Optional[str] = None,
    raw_value: Any = None,
    status_when_true: Literal["ok", "issue", "unknown"] = "ok",
    status_when_false: Literal["ok", "issue", "unknown"] = "issue",
) -> ChecklistAnswer:
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
    if value is None:
        return _answer_missing(raw_value)
    has_issue = bool(value)
    code = "bool_no" if not has_issue else "bool_yes"
    text = _answer_text(code, _BOOL_NO if not has_issue else _BOOL_YES)
    status = "ok" if not has_issue else "issue"
    stored_raw = value if raw_value is None else raw_value
    return ChecklistAnswer(code=code, text=text, status=status, raw_value=stored_raw)


def _availability_from_count(count: Optional[int]) -> ChecklistAnswer:
    if count is None:
        return _answer_missing(count)
    has_items = count > 0
    code = "available_yes" if has_items else "available_no"
    text = _answer_text(code, _AVAILABLE_YES if has_items else _AVAILABLE_NO)
    status = "ok" if has_items else "issue"
    return ChecklistAnswer(code=code, text=text, status=status, raw_value=count)


def _exposure_detail_answer(value: Optional[bool]) -> ChecklistAnswer:
    if value is None:
        return _answer_missing(value)
    code = "exists_yes" if value else "exists_no"
    text = _answer_text(code, _EXISTS_YES if value else _EXISTS_NO)
    status = "issue" if value else "ok"
    return ChecklistAnswer(code=code, text=text, status=status, raw_value=value)


def _inspection_answer(flag: Optional[bool]) -> ChecklistAnswer:
    if flag is None:
        return _answer_missing(flag)
    code = "inspection_found_yes" if flag else "inspection_found_no"
    text = _INSPECTION_FOUND if flag else _INSPECTION_NOT_FOUND
    status = "issue" if flag else "ok"
    return ChecklistAnswer(code=code, text=text, status=status, raw_value=flag)


def build_checklist_document(
    company: Mapping[str, Any],
    dd: Optional[Mapping[str, Any]],
) -> ChecklistDocument:
    reg_date_value = company.get("reg_date")
    reg_date_obj: Optional[date]
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

    dd_map = dict(dd) if dd else {}

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


# Healthcheck
@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"ok": True}


class InitRequest(BaseModel):
    config_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

@app.post("/admin/init")
def init_db(req: InitRequest):
    """Create schema from scratch and load a fresh dataset."""
    if not req.config_path and not req.config:
        raise HTTPException(400, "Provide config_path or inline config")
    cfg = req.config or (yaml.safe_load(open(req.config_path, "r", encoding="utf-8")) if req.config_path else None)
    if cfg is None:
        raise HTTPException(400, "Failed to read config")
    init_schema(reset=True)
    dataset = generate_dataset(cfg)
    load_to_db(dataset, if_exists="append")
    # return counts
    with engine.connect() as conn:
        counts = {}
        for t in ["company","person","ownership","financials","court_case","sanction_subject","risk_scores"]:
            counts[t] = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
    return {"status":"ok","counts":counts}

class AddRequest(BaseModel):
    n: int = 50
    distribution: Optional[Dict[str,int]] = None
    config_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

@app.post("/admin/add")
def add_records(req: AddRequest):
    """Add N companies (and linked records) to existing DB."""
    if not req.config_path and not req.config:
        raise HTTPException(400, "Provide config_path or inline config")
    cfg = req.config or (yaml.safe_load(open(req.config_path, "r", encoding="utf-8")) if req.config_path else None)
    if cfg is None:
        raise HTTPException(400, "Failed to read config")
    # override sizes
    cfg = dict(cfg)  # shallow copy
    cfg["general"] = dict(cfg["general"])
    cfg["general"]["n_companies"] = req.n
    # more persons roughly proportional
    cfg["general"]["n_persons"] = max(req.n * 2, 60)
    if req.distribution:
        cfg["classes"] = dict(cfg["classes"])
        cfg["classes"]["distribution"] = req.distribution
    dataset = generate_dataset(cfg)
    load_to_db(dataset, if_exists="append")
    return {"status":"ok","added": req.n}


@app.get("/admin/tail", response_model=List[CompanyOut])
def admin_tail(limit: int = Query(10, ge=1, le=100)):
    """Return the most recently registered companies (default 10)."""
    sql = """
    SELECT c.id, c.name, c.inn, c.ogrn, c.status, c.okved_main, c.reg_date, c.address,
           r.grade, r.solvency, r.reliability, r.compliance_flag
      FROM company c
      LEFT JOIN risk_scores r ON r.company_id = c.id
     ORDER BY c.reg_date DESC NULLS LAST, c.id DESC
     LIMIT :limit
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]


@app.get("/admin/export-companies")
def export_companies(limit: Optional[int] = Query(None, ge=1)):
    """Dump companies with risk & due diligence metrics to CSV."""
    base_sql = """
    SELECT c.id AS company_id, c.name, c.inn, c.ogrn, c.status, c.okved_main, c.reg_date, c.address,
           r.grade, r.solvency, r.reliability, r.compliance_flag,
           dd.egrul_has_invalid_data, dd.status_issue, dd.identity_matches, dd.age_years,
           dd.staff_count, dd.staff_sufficient, dd.has_quality_docs, dd.quality_docs_details,
           dd.has_assets, dd.assets_total_value,
           dd.tax_debt, dd.fssp_debt, dd.open_credit_lines, dd.has_leasing,
           dd.active_court_cases, dd.executive_debt, dd.gov_contracts_count,
           dd.gov_contracts_total, dd.in_rnp, dd.mass_registration,
           dd.director_disqualified, dd.director_nominee, dd.has_power_of_attorney,
           dd.blocked_accounts, dd.blocked_banks, dd.tax_clearance_recent,
           dd.regulatory_violations, dd.regulatory_violations_details
      FROM company c
      LEFT JOIN risk_scores r ON r.company_id = c.id
      LEFT JOIN due_diligence dd ON dd.company_id = c.id
     ORDER BY c.reg_date DESC NULLS LAST, c.id DESC
    """
    params: Dict[str, Any] = {}
    if limit is not None:
        base_sql += " LIMIT :limit"
        params["limit"] = limit
    df = pd.read_sql_query(text(base_sql), engine, params=params)
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    filename_suffix = f"{limit}" if limit is not None else "all"
    headers = {
        "Content-Disposition": f"attachment; filename=companies_{filename_suffix}.csv"
    }
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv", headers=headers)

@app.get("/search", response_model=List[CompanyOut])
def search(name: Optional[str] = Query(None, description="substring match (ILIKE)"),
           inn: Optional[str] = Query(None),
           include_checklist: bool = Query(False, description="attach checklist document to results")):
    if not name and not inn:
        raise HTTPException(400, "Specify name or inn")
    sql = """
    SELECT c.id, c.name, c.inn, c.ogrn, c.status, c.okved_main, c.reg_date, c.address,
           r.grade, r.solvency, r.reliability, r.compliance_flag
      FROM company c
      LEFT JOIN risk_scores r ON r.company_id = c.id
    """
    params = {}
    if inn:
        sql += " WHERE c.inn = :inn"
        params["inn"] = inn
    elif name:
        sql += " WHERE c.name ILIKE :q"
        params["q"] = f"%{name}%"
    sql += " ORDER BY c.name LIMIT 100"
    results: List[Dict[str, Any]] = []
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
        for row in rows:
            row_dict = dict(row)
            if include_checklist:
                dd = conn.execute(text("SELECT * FROM due_diligence WHERE company_id=:id"), {"id": row_dict["id"]}).mappings().first()
                dd_dict = dict(dd) if dd else None
                row_dict["checklist_document"] = build_checklist_document(row_dict, dd_dict)
            results.append(row_dict)
    return results

@app.get("/by-inn/{inn}", response_model=CompanyOut)
def by_inn(inn: str):
    sql = """
    SELECT c.id, c.name, c.inn, c.ogrn, c.status, c.okved_main, c.reg_date, c.address,
           r.grade, r.solvency, r.reliability, r.compliance_flag
      FROM company c
      LEFT JOIN risk_scores r ON r.company_id = c.id
     WHERE c.inn = :inn
     LIMIT 1
    """
    with engine.connect() as conn:
        row = conn.execute(text(sql), {"inn": inn}).mappings().first()
        if not row:
            raise HTTPException(404, "Not found")
        dd = conn.execute(text("SELECT * FROM due_diligence WHERE company_id=:id"), {"id": row["id"]}).mappings().first()
    row_dict = dict(row)
    dd_dict = dict(dd) if dd else None
    row_dict["checklist_document"] = build_checklist_document(row_dict, dd_dict)
    return row_dict


@app.get(
    "/check",
    response_model=ChecklistResponse,
    summary="Сформировать чек-лист по контрагенту",
    tags=["Checklist"],
)
def run_check(
    company_id: Optional[UUID] = Query(None, description="Company identifier"),
    inn: Optional[str] = Query(None, description="Exact INN match"),
    name: Optional[str] = Query(None, description="Company name (ILIKE match)"),
):
    """Возвращает структурированный чек-лист должной осмотрительности по найденному контрагенту.

    Укажите один из параметров идентификации (UUID компании, ИНН или часть названия).
    В ответе придут:

    * реквизиты и скоринговые показатели компании;
    * список пунктов памятки с кодами, вопросами, нормализованными ответами и дополнительными данными;
    * метаданные проверки (локаль, дата формирования, человеко-читаемые подписи сервисных полей).
    """
    if not any([company_id, inn, name]):
        raise HTTPException(400, "Specify company_id, inn, or name")

    sql = """
    SELECT c.id, c.name, c.inn, c.ogrn, c.status, c.okved_main, c.reg_date, c.address,
           r.grade, r.solvency, r.reliability, r.compliance_flag
      FROM company c
      LEFT JOIN risk_scores r ON r.company_id = c.id
    """
    params: Dict[str, Any] = {}

    if company_id is not None:
        sql += " WHERE c.id = :company_id"
        params["company_id"] = company_id
    elif inn is not None:
        sql += " WHERE c.inn = :inn"
        params["inn"] = inn
    else:
        sql += " WHERE c.name ILIKE :name"
        params["name"] = f"%{name}%"
    sql += " ORDER BY c.name LIMIT 1"

    with engine.connect() as conn:
        row = conn.execute(text(sql), params).mappings().first()
        if not row:
            raise HTTPException(404, "Company not found")
        dd = conn.execute(
            text("SELECT * FROM due_diligence WHERE company_id = :id"),
            {"id": row["id"]},
        ).mappings().first()

    row_dict = dict(row)
    dd_dict = dict(dd) if dd else None
    document = build_checklist_document(row_dict, dd_dict)
    return ChecklistResponse(checklist_document=document)

@app.get("/company/{company_id}")
def company_details(company_id: str):
    with engine.connect() as conn:
        comp = conn.execute(text("""
            SELECT c.*, r.grade, r.solvency, r.reliability, r.compliance_flag, r.sanctioned_control_share
            FROM company c LEFT JOIN risk_scores r ON r.company_id=c.id
            WHERE c.id=:id
        """), {"id": company_id}).mappings().first()
        if not comp: raise HTTPException(404, "Not found")
        fins = conn.execute(text("""SELECT * FROM financials WHERE company_id=:id ORDER BY year"""), {"id": company_id}).mappings().all()
        courts = conn.execute(text("""SELECT * FROM court_case WHERE company_id=:id ORDER BY filed_at DESC LIMIT 50"""), {"id": company_id}).mappings().all()
        owners = conn.execute(text("""SELECT * FROM ownership WHERE target_company_id=:id"""), {"id": company_id}).mappings().all()
        dd = conn.execute(text("""SELECT * FROM due_diligence WHERE company_id=:id"""), {"id": company_id}).mappings().first()
        comp_dict = dict(comp)
        dd_dict = dict(dd) if dd else None
        if dd_dict:
            for key in ["gov_contracts_total", "assets_total_value"]:
                if key in dd_dict:
                    dd_dict[key] = _to_float(dd_dict[key])
        checklist_document = build_checklist_document(comp_dict, dd_dict)
        return {
            "company": comp_dict,
            "financials": [dict(x) for x in fins],
            "court_cases": [dict(x) for x in courts],
            "ownership": [dict(x) for x in owners],
            "due_diligence": dd_dict,
            "checklist_document": checklist_document
        }

# Ensure schema on startup (no reset)
@app.on_event("startup")
def _startup():
    ensure_schema()
