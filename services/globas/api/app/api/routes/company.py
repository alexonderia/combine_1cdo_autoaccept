"""Маршруты для поиска и получения сведений о компаниях."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from ...application import AppContainer
from ...dependencies import container_dependency
from ...models.checklist import ChecklistResponse, CompanyOut
from ...services.checklist import build_checklist_document, to_float

router = APIRouter(tags=["companies"])


@router.get("/search", response_model=List[CompanyOut])
def search(
    name: Optional[str] = Query(None, description="substring match (ILIKE)"),
    inn: Optional[str] = Query(None),
    include_checklist: bool = Query(False, description="attach checklist document to results"),
    container: AppContainer = Depends(container_dependency),
) -> List[Dict[str, Any]]:
    """Выполняет поиск компаний по части названия или ИНН."""

    if not name and not inn:
        raise HTTPException(400, "Specify name or inn")

    sql = """
    SELECT c.id, c.name, c.inn, c.ogrn, c.status, c.okved_main, c.reg_date, c.address,
           r.grade, r.solvency, r.reliability, r.compliance_flag
      FROM company c
      LEFT JOIN risk_scores r ON r.company_id = c.id
    """
    params: Dict[str, Any] = {}

    if inn:
        sql += " WHERE c.inn = :inn"
        params["inn"] = inn
    elif name:
        sql += " WHERE c.name ILIKE :q"
        params["q"] = f"%{name}%"

    sql += " ORDER BY c.name LIMIT 100"

    results: List[Dict[str, Any]] = []
    with container.engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
        for row in rows:
            row_dict = dict(row)
            if include_checklist:
                dd = conn.execute(
                    text("SELECT * FROM due_diligence WHERE company_id=:id"),
                    {"id": row_dict["id"]},
                ).mappings().first()
                dd_dict = dict(dd) if dd else None
                row_dict["checklist_document"] = build_checklist_document(row_dict, dd_dict)
            results.append(row_dict)
    return results


@router.get("/by-inn/{inn}", response_model=CompanyOut)
def by_inn(
    inn: str,
    container: AppContainer = Depends(container_dependency),
) -> Dict[str, Any]:
    """Возвращает информацию о компании по точному совпадению ИНН."""

    sql = """
    SELECT c.id, c.name, c.inn, c.ogrn, c.status, c.okved_main, c.reg_date, c.address,
           r.grade, r.solvency, r.reliability, r.compliance_flag
      FROM company c
      LEFT JOIN risk_scores r ON r.company_id = c.id
     WHERE c.inn = :inn
     LIMIT 1
    """

    with container.engine.connect() as conn:
        row = conn.execute(text(sql), {"inn": inn}).mappings().first()
        if not row:
            raise HTTPException(404, "Not found")
        dd = conn.execute(
            text("SELECT * FROM due_diligence WHERE company_id=:id"),
            {"id": row["id"]},
        ).mappings().first()

    row_dict = dict(row)
    dd_dict = dict(dd) if dd else None
    row_dict["checklist_document"] = build_checklist_document(row_dict, dd_dict)
    return row_dict


@router.get(
    "/check",
    response_model=ChecklistResponse,
    summary="Сформировать чек-лист по контрагенту",
    tags=["Checklist"],
)
def run_check(
    company_id: Optional[UUID] = Query(None, description="Company identifier"),
    inn: Optional[str] = Query(None, description="Exact INN match"),
    name: Optional[str] = Query(None, description="Company name (ILIKE match)"),
    container: AppContainer = Depends(container_dependency),
) -> ChecklistResponse:
    """Формирует структурированный чек-лист по найденному контрагенту."""

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

    with container.engine.connect() as conn:
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


@router.get("/company/{company_id}")
def company_details(
    company_id: str,
    container: AppContainer = Depends(container_dependency),
) -> Dict[str, Any]:
    """Возвращает подробные сведения о компании."""

    sql_company = """
        SELECT c.*, r.grade, r.solvency, r.reliability, r.compliance_flag, r.sanctioned_control_share
          FROM company c LEFT JOIN risk_scores r ON r.company_id=c.id
         WHERE c.id=:id
    """

    sql_financials = "SELECT * FROM financials WHERE company_id=:id ORDER BY year"
    sql_courts = "SELECT * FROM court_case WHERE company_id=:id ORDER BY filed_at DESC LIMIT 50"
    sql_owners = "SELECT * FROM ownership WHERE target_company_id=:id"
    sql_due_diligence = "SELECT * FROM due_diligence WHERE company_id=:id"

    with container.engine.connect() as conn:
        comp = conn.execute(text(sql_company), {"id": company_id}).mappings().first()
        if not comp:
            raise HTTPException(404, "Not found")
        fins = conn.execute(text(sql_financials), {"id": company_id}).mappings().all()
        courts = conn.execute(text(sql_courts), {"id": company_id}).mappings().all()
        owners = conn.execute(text(sql_owners), {"id": company_id}).mappings().all()
        dd = conn.execute(text(sql_due_diligence), {"id": company_id}).mappings().first()

    comp_dict = dict(comp)
    dd_dict = dict(dd) if dd else None
    if dd_dict:
        for key in ["gov_contracts_total", "assets_total_value"]:
            if key in dd_dict:
                dd_dict[key] = to_float(dd_dict[key])
    checklist_document = build_checklist_document(comp_dict, dd_dict)

    return {
        "company": comp_dict,
        "financials": [dict(x) for x in fins],
        "court_cases": [dict(x) for x in courts],
        "ownership": [dict(x) for x in owners],
        "due_diligence": dd_dict,
        "checklist_document": checklist_document,
    }
