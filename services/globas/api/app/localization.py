"""Checklist text resources and localization helpers."""
from __future__ import annotations

import json
import logging
import os
from copy import deepcopy
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CHECKLIST_TEXTS: Dict[str, Any] = {
    "answers": {
        "bool_yes": "Да",
        "bool_no": "Нет",
        "missing": "Нет данных",
        "available_yes": "Имеется",
        "available_no": "Не имеется",
        "collection_yes": "Имеются",
        "collection_no": "Не имеются",
        "exists_yes": "Есть",
        "exists_no": "Нет",
        "inspection_found_yes": "Выявляли",
        "inspection_found_no": "Не выявляли",
    },
    "exposure_labels": {
        "tax_debt": "Налоговые задолженности",
        "fssp_debt": "Исполнительные производства ФССП",
        "open_credit_lines": "Открытые кредитные линии",
        "leasing": "Лизинговые обязательства",
    },
    "locale": "ru-RU",
    "questions": {
        "egrul_invalid_data": "Нет ли в реестре ЕГРЮЛ отметки о недостоверности сведений",
        "liquidation_bankruptcy": "Не находится ли контрагент в процессе ликвидации, банкротства, реорганизации или смены юридического адреса",
        "identity_matches": "Совпадают ли ИНН, ОГРН, адрес, директор и контактные данные с представленными контрагентом",
        "company_age_requirement": "Срок действия компании (от 3-х лет в идеале)",
        "staff_sufficiency": "Достаточно ли у контрагента персонала для исполнения сделки",
        "quality_docs": "Наличие паспортов качества, сертификатов соответствия, СРО, лицензий",
        "has_assets": "Есть ли у компании финансовые активы, недвижимость или другие основные средства",
        "tax_debt_and_obligations": "Нет ли у контрагента долгов по налогам, исполнительных листов ФССП, кредитным линиям и лизингу",
        "active_court_cases": "Нет ли в отношении контрагента дел о понуждении исполнить обязательство или вернуть деньги",
        "executive_debt": "Нет ли у контрагента долгов по исполнительным листам",
        "gov_contracts_experience": "Опыт работы по гос. контрактам за последние 3 года в рамках 44-ФЗ и 223-ФЗ",
        "in_rnp": "Не состоит ли контрагент в реестре недобросовестных поставщиков",
        "mass_registration": "Не зарегистрирован ли контрагент по адресу массовой регистрации",
        "director_disqualified": "Не состоит ли директор в реестре дисквалифицированных лиц",
        "director_nominee": "Не состоит ли директор в реестре номинальных руководителей",
        "power_of_attorney": "Наличие доверенностей на должностных лиц, являющихся подписантами договора",
        "blocked_accounts": "Какие банки заблокировали контрагенту счета",
        "tax_clearance_certificate": "Наличие справки ФНС об отсутствии задолженности по налогам и сборам",
        "regulatory_violations": "Выявляли ли госорганы нарушения при проверках и какие",
    },
    "metadata": {
        "title": "Чек-лист к памятке о порядке проведения должной осмотрительности",
        "fields": {
            "checked_at": "Дата проверки",
            "checked_by": "Кто проверял",
            "digital_signature": "Подпись (ПЭП)",
        },
    },
}


def _deep_update(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in overrides.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            base[key] = _deep_update(dict(base[key]), value)
        else:
            base[key] = value
    return base


def _load_texts_from_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        if path.endswith((".yml", ".yaml")):
            data = yaml.safe_load(handle)
        else:
            data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Checklist texts file must define a dictionary at the top level")
    return data


def load_checklist_texts() -> Dict[str, Any]:
    texts = deepcopy(DEFAULT_CHECKLIST_TEXTS)
    path = os.getenv("CHECKLIST_TEXTS_PATH", "/app/config/ruRU/checklist_texts.yml")
    if path and os.path.exists(path):
        try:
            overrides = _load_texts_from_file(path)
            texts = _deep_update(texts, overrides)
        except Exception as exc:  # noqa: BLE001 - log and continue with defaults
            logger.warning("Failed to load checklist texts from %s: %s", path, exc)
    return texts


CHECKLIST_TEXTS = load_checklist_texts()

