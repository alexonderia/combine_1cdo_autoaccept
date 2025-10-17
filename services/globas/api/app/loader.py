from sqlalchemy import text
from .db import engine, ensure_schema, drop_schema
import pandas as pd

TABLE_MAP = {
    "companies": "company",
    "persons": "person",
    "ownership": "ownership",
    "financials": "financials",
    "court_cases": "court_case",
    "sanctions": "sanction_subject",
    "risk_scores": "risk_scores",
    "due_diligence": "due_diligence"
}

def init_schema(reset: bool = False):
    if reset:
        drop_schema()
    ensure_schema()

def load_to_db(dataset: dict, if_exists: str = "append"):
    with engine.begin() as conn:
        for key, df in dataset.items():
            table = TABLE_MAP[key]
            df.to_sql(table, con=conn, index=False, if_exists=if_exists, method="multi", chunksize=1000)
