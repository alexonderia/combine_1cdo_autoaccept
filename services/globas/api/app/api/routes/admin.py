"""Административные эндпоинты для управления синтетическими данными."""

from __future__ import annotations

from io import StringIO
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from pydantic import BaseModel

from ...application import AppContainer
from ...dependencies import container_dependency
from ...loader import init_schema, load_to_db
from ...generator_core import generate_dataset
from ...models.checklist import CompanyOut

router = APIRouter(prefix="/admin", tags=["admin"])


class InitRequest(BaseModel):
    """Параметры инициализации схемы и первичной загрузки."""

    config_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


@router.post("/init")
def init_db(
    req: InitRequest,
    container: AppContainer = Depends(container_dependency),
) -> Dict[str, Any]:
    """Полностью пересоздаёт схему и заполняет её новым датасетом."""

    if not req.config_path and not req.config:
        raise HTTPException(400, "Provide config_path or inline config")

    cfg = req.config
    if cfg is None and req.config_path:
        with open(req.config_path, "r", encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
    if cfg is None:
        raise HTTPException(400, "Failed to read config")

    init_schema(reset=True)
    dataset = generate_dataset(cfg)
    load_to_db(dataset, if_exists="append")

    with container.engine.connect() as conn:
        tables = [
            "company",
            "person",
            "ownership",
            "financials",
            "court_case",
            "sanction_subject",
            "risk_scores",
        ]
        counts = {
            table: conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            for table in tables
        }

    return {"status": "ok", "counts": counts}


class AddRequest(BaseModel):
    """Параметры дозагрузки новых записей."""

    n: int = 50
    distribution: Optional[Dict[str, int]] = None
    config_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


@router.post("/add")
def add_records(
    req: AddRequest,
    container: AppContainer = Depends(container_dependency),
) -> Dict[str, Any]:
    """Добавляет указанное количество компаний к существующим данным."""

    if not req.config_path and not req.config:
        raise HTTPException(400, "Provide config_path or inline config")

    cfg = req.config
    if cfg is None and req.config_path:
        with open(req.config_path, "r", encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
    if cfg is None:
        raise HTTPException(400, "Failed to read config")

    cfg = dict(cfg)
    cfg.setdefault("general", {})
    cfg["general"] = dict(cfg["general"])
    cfg["general"]["n_companies"] = req.n
    cfg["general"]["n_persons"] = max(req.n * 2, 60)

    if req.distribution:
        cfg.setdefault("classes", {})
        cfg["classes"] = dict(cfg["classes"])
        cfg["classes"]["distribution"] = req.distribution

    dataset = generate_dataset(cfg)
    load_to_db(dataset, if_exists="append")

    return {"status": "ok", "added": req.n}


@router.get("/tail", response_model=List[CompanyOut])
def admin_tail(
    limit: int = Query(10, ge=1, le=100),
    container: AppContainer = Depends(container_dependency),
) -> List[Dict[str, Any]]:
    """Возвращает N последних зарегистрированных компаний."""

    sql = """
    SELECT c.id, c.name, c.inn, c.ogrn, c.status, c.okved_main, c.reg_date, c.address,
           r.grade, r.solvency, r.reliability, r.compliance_flag
      FROM company c
      LEFT JOIN risk_scores r ON r.company_id = c.id
     ORDER BY c.reg_date DESC NULLS LAST, c.id DESC
     LIMIT :limit
    """

    with container.engine.connect() as conn:
        rows = conn.execute(text(sql), {"limit": limit}).mappings().all()
    return [dict(row) for row in rows]


@router.get("/export-companies")
def export_companies(
    limit: Optional[int] = Query(None, ge=1),
    container: AppContainer = Depends(container_dependency),
):
    """Выгружает данные компаний и метрик в CSV."""

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

    df = pd.read_sql_query(text(base_sql), container.engine, params=params)
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    filename_suffix = f"{limit}" if limit is not None else "all"
    headers = {"Content-Disposition": f"attachment; filename=companies_{filename_suffix}.csv"}

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers=headers,
    )
