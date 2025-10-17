from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://globas:globas@db:5432/globas")

engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True)

DDL = '''
CREATE TABLE IF NOT EXISTS company(
  id UUID PRIMARY KEY,
  inn TEXT UNIQUE,
  ogrn TEXT,
  name TEXT,
  status TEXT,
  okved_main TEXT,
  reg_date DATE,
  address TEXT,
  mass_address BOOLEAN DEFAULT FALSE,
  director_person_id UUID,
  director_changes_last_year INT
);

CREATE TABLE IF NOT EXISTS person(
  id UUID PRIMARY KEY,
  full_name TEXT,
  inn TEXT
);

CREATE TABLE IF NOT EXISTS ownership(
  id UUID PRIMARY KEY,
  holder_type TEXT CHECK(holder_type IN ('company','person')),
  holder_id UUID,
  target_company_id UUID,
  share NUMERIC(5,2),
  via TEXT
);
CREATE INDEX IF NOT EXISTS ix_ownership_target ON ownership(target_company_id);

CREATE TABLE IF NOT EXISTS financials(
  company_id UUID,
  year INT,
  revenue NUMERIC,
  profit NUMERIC,
  assets NUMERIC,
  liabilities NUMERIC,
  PRIMARY KEY(company_id, year)
);

CREATE TABLE IF NOT EXISTS court_case(
  id UUID PRIMARY KEY,
  company_id UUID,
  kind TEXT,
  role TEXT,
  amount NUMERIC,
  status TEXT,
  filed_at DATE
);

CREATE TABLE IF NOT EXISTS sanction_subject(
  id UUID PRIMARY KEY,
  subject_type TEXT,
  subject_id UUID,
  list_name TEXT,
  authority TEXT,
  reason TEXT,
  date_added DATE
);
CREATE INDEX IF NOT EXISTS ix_sanction_subject_subject ON sanction_subject(subject_type, subject_id);

CREATE TABLE IF NOT EXISTS risk_scores(
  company_id UUID PRIMARY KEY,
  solvency INT,
  reliability INT,
  compliance_flag TEXT,
  sanctioned_control_share NUMERIC(6,3),
  grade TEXT
);

CREATE TABLE IF NOT EXISTS due_diligence(
  company_id UUID PRIMARY KEY,
  egrul_has_invalid_data BOOLEAN,
  status_issue BOOLEAN,
  identity_matches BOOLEAN,
  age_years INT,
  staff_count INT,
  staff_sufficient BOOLEAN,
  has_quality_docs BOOLEAN,
  quality_docs_details TEXT,
  has_assets BOOLEAN,
  assets_total_value NUMERIC,
  tax_debt BOOLEAN,
  fssp_debt BOOLEAN,
  open_credit_lines BOOLEAN,
  has_leasing BOOLEAN,
  active_court_cases BOOLEAN,
  executive_debt BOOLEAN,
  gov_contracts_count INT,
  gov_contracts_total NUMERIC,
  in_rnp BOOLEAN,
  mass_registration BOOLEAN,
  director_disqualified BOOLEAN,
  director_nominee BOOLEAN,
  has_power_of_attorney BOOLEAN,
  blocked_accounts BOOLEAN,
  blocked_banks TEXT,
  tax_clearance_recent BOOLEAN,
  regulatory_violations BOOLEAN,
  regulatory_violations_details TEXT
);
ALTER TABLE due_diligence ADD COLUMN IF NOT EXISTS quality_docs_details TEXT;
ALTER TABLE due_diligence ADD COLUMN IF NOT EXISTS assets_total_value NUMERIC;
ALTER TABLE due_diligence ADD COLUMN IF NOT EXISTS regulatory_violations_details TEXT;

-- Helpful indexes
CREATE INDEX IF NOT EXISTS ix_company_inn ON company(inn);
CREATE INDEX IF NOT EXISTS ix_company_name ON company USING GIN (to_tsvector('russian', name));
'''

DROP = '''
DROP TABLE IF EXISTS due_diligence;
DROP TABLE IF EXISTS risk_scores;
DROP TABLE IF EXISTS sanction_subject;
DROP TABLE IF EXISTS court_case;
DROP TABLE IF EXISTS financials;
DROP TABLE IF EXISTS ownership;
DROP TABLE IF EXISTS company;
DROP TABLE IF EXISTS person;
'''

def drop_schema():
    with engine.begin() as conn:
        conn.execute(text(DROP))

def ensure_schema():
    with engine.begin() as conn:
        conn.execute(text(DDL))
