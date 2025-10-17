import random, math, uuid
from collections import defaultdict, deque, Counter
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import yaml
import json

DEFAULT_TODAY = date(2025,10,6)

def load_config(path_or_dict):
    if isinstance(path_or_dict, dict):
        return path_or_dict
    with open(path_or_dict, 'r', encoding='utf-8') as f:
        if path_or_dict.endswith(('.yml','.yaml')):
            return yaml.safe_load(f)
        return json.load(f)

def sanctioned_control_share(company_id, incoming, sanctioned_subjects, max_depth=6, cutoff=0.005):
    total = 0.0
    dq = deque()
    dq.append((company_id, 1.0, 0))
    visited_edges = set()
    while dq:
        node, path_share, depth = dq.popleft()
        if depth > max_depth or path_share < cutoff:
            continue
        for (ht, hid, share) in incoming.get(node, []):
            edge = (ht, hid, node)
            if edge in visited_edges:
                continue
            visited_edges.add(edge)
            new_share = path_share * (share / 100.0)
            if (ht, hid) in sanctioned_subjects:
                total += new_share
            if ht == "company":
                dq.append((hid, new_share, depth+1))
    return total

def compute_scores(companies_df, financials_df, court_df, ownership_df, sanctions_df, today, params):
    incoming = defaultdict(list)
    for _, r in ownership_df.iterrows():
        incoming[r["target_company_id"]].append((r["holder_type"], r["holder_id"], float(r["share"])))
    sanctioned_subjects = set((r["subject_type"], r["subject_id"]) for _, r in sanctions_df.iterrows())

    rows = []
    for _, row in companies_df.iterrows():
        cid = row["id"]
        reg_date = datetime.fromisoformat(row["reg_date"]).date()
        age_years = (today - reg_date).days / 365.25
        status = row["status"]
        director_changes = int(row.get("director_changes_last_year", 0))
        mass_address = bool(row.get("mass_address", False))

        f_last = financials_df[(financials_df["company_id"]==cid) & (financials_df["year"]==params["financials"]["last_year"])]
        if f_last.empty:
            f_last = financials_df[financials_df["company_id"]==cid].sort_values("year").tail(1)

        rev = float(f_last["revenue"].iloc[0]) if not f_last.empty else 0.0
        profit = float(f_last["profit"].iloc[0]) if not f_last.empty else 0.0
        assets = float(f_last["assets"].iloc[0]) if not f_last.empty else 0.0
        liabilities = float(f_last["liabilities"].iloc[0]) if not f_last.empty else 0.0

        margin = (profit / rev) if rev > 0 else -0.2
        ratio = (liabilities / assets) if assets > 0 else 1.2

        # Solvency
        solv = params["risk"]["solvency"]["base"]
        for br in params["risk"]["solvency"]["margin_brackets"]:
            if "gt" in br and margin > br["gt"]:
                solv += br["add"]
            elif "lt" in br and margin < br["lt"]:
                solv += br["add"]
        for br in params["risk"]["solvency"]["ratio_brackets"]:
            if "le" in br and ratio <= br["le"]:
                solv += br["add"]
            elif "gt" in br and ratio > br["gt"]:
                solv += br["add"]

        x = params["risk"]["solvency"]["lawsuit_x"]
        per = params["risk"]["solvency"]["lawsuit_penalty_per_x10"]
        cap = params["risk"]["solvency"]["lawsuit_penalty_cap"]
        c12 = court_df[(court_df["company_id"]==cid) & (pd.to_datetime(court_df["filed_at"]).dt.date >= (today - timedelta(days=365)))]
        sum12 = float(c12["amount"].sum()) if not c12.empty else 0.0
        solv -= min(cap, sum12 / x * per)
        solv = int(round(max(0, min(100, solv))))

        # Reliability
        rel = params["risk"]["reliability"]["base"]
        if age_years > params["risk"]["reliability"]["age_bonus_after_years"]:
            rel += params["risk"]["reliability"]["age_bonus"]
        elif age_years < params["risk"]["reliability"]["young_years"]:
            rel -= params["risk"]["reliability"]["young_penalty"]
        if director_changes > params["risk"]["reliability"]["director_changes_threshold"]:
            rel -= params["risk"]["reliability"]["director_changes_penalty"]
        if mass_address:
            rel -= params["risk"]["reliability"]["mass_address_penalty"]
        if status != "ACTIVE":
            rel -= params["risk"]["reliability"]["non_active_penalty"]
        rel = int(round(max(0, min(100, rel))))

        # Compliance
        sc_share = sanctioned_control_share(cid, incoming, sanctioned_subjects,
                                            max_depth=params["risk"]["compliance"]["max_depth"],
                                            cutoff=params["risk"]["compliance"]["cutoff"])
        direct_sanction = ("company", cid) in sanctioned_subjects
        if direct_sanction or sc_share >= params["risk"]["compliance"]["critical_threshold"]:
            compliance_flag = "critical"
        elif sc_share >= params["risk"]["compliance"]["elevated_threshold"]:
            compliance_flag = "elevated"
        else:
            compliance_flag = "ok"

        if (compliance_flag == "critical" or
            solv < params["grade_rules"]["solvency_red_lt"] or
            rel < params["grade_rules"]["reliability_red_lt"]):
            grade = "red"
        elif (compliance_flag == "elevated" or
              solv < params["grade_rules"]["solvency_green_ge"] or
              rel < params["grade_rules"]["reliability_green_ge"]):
            grade = "yellow"
        else:
            grade = "green"

        rows.append({
            "company_id": cid,
            "solvency": solv,
            "reliability": rel,
            "compliance_flag": compliance_flag,
            "sanctioned_control_share": round(sc_share, 3),
            "grade": grade
        })
    return pd.DataFrame(rows)

def generate_dataset(cfg):
    rng = random.Random(cfg["general"].get("seed", 42))
    np.random.seed(cfg["general"].get("seed", 42))
    today = DEFAULT_TODAY
    if "today" in cfg["general"]:
        y,m,d = map(int, str(cfg["general"]["today"]).split("-"))
        today = date(y,m,d)

    N = int(cfg["general"]["n_companies"])
    num_persons = int(cfg["general"]["n_persons"])
    dist_target = cfg["classes"]["distribution"]

    # --- Dictionaries (inline arrays or paths to txt)
    def load_list(key):
        val = cfg["dictionaries"].get(key)
        if isinstance(val, list):
            return val
        # read file
        with open(val, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    surnames = load_list("surnames")
    first_names = load_list("first_names")
    patronymics = load_list("patronymics")
    comp_adjs = load_list("company_adjectives")
    comp_nouns = load_list("company_nouns")
    cities = load_list("cities")
    streets = load_list("streets")
    okveds = load_list("okveds")

    def make_person_name():
        return f"{rng.choice(surnames)} {rng.choice(first_names)} {rng.choice(patronymics)}"

    def make_company_name():
        return f"ООО «{rng.choice(comp_adjs)}{rng.choice(comp_nouns)}»"

    def rnd_digits(n): return "".join(str(rng.randint(0,9)) for _ in range(n))
    def inn_company(): return rnd_digits(10)
    def inn_person(): return rnd_digits(12)
    def ogrn(): return rnd_digits(13)

    labels = (["red"] * dist_target["red"] + ["yellow"] * dist_target["yellow"] + ["green"] * dist_target["green"])
    rng.shuffle(labels)

    persons = [{
        "id": str(uuid.uuid4()),
        "full_name": make_person_name(),
        "inn": inn_person()
    } for _ in range(num_persons)]
    persons_df = pd.DataFrame(persons)

    mass_addresses_pool = cfg["addresses"].get("predefined_mass_addresses", [])
    if not mass_addresses_pool:
        mass_addresses_pool = [f"г. Москва, ул. Новая, д. 12, оф. {i}" for i in cfg["addresses"].get("mass_addresses_offices", [101,202,303,404,505])]

    def make_address(force_mass=False):
        if force_mass and mass_addresses_pool:
            return rng.choice(mass_addresses_pool)
        city = rng.choice(cities); street = rng.choice(streets)
        house = rng.randint(1, 120); office = rng.randint(1, 999)
        return f"г. {city}, ул. {street}, д. {house}, оф. {office}"

    companies = []
    for i in range(N):
        lbl = labels[i]
        if lbl == "green":
            status = "ACTIVE"
        elif lbl == "yellow":
            status = rng.choices(
                ['ACTIVE', 'LIQUIDATION', 'REORGANIZATION', 'ADDRESS_CHANGE'],
                weights=[0.6, 0.15, 0.15, 0.1]
            )[0]
        else:
            status = rng.choices(
                ['ACTIVE', 'LIQUIDATION', 'BANKRUPTCY', 'REORGANIZATION', 'ADDRESS_CHANGE'],
                weights=[0.35, 0.25, 0.2, 0.12, 0.08]
            )[0]
        if lbl == "green":
            start_year = rng.randint(*cfg["companies"]["reg_year_range"]["green"])
        elif lbl == "yellow":
            start_year = rng.randint(*cfg["companies"]["reg_year_range"]["yellow"])
        else:
            start_year = rng.randint(*cfg["companies"]["reg_year_range"]["red"])
        reg_date = date(start_year, rng.randint(1,12), rng.randint(1,28))
        if reg_date > today: reg_date = today
        okved = rng.choice(okveds)
        force_mass = rng.random() < cfg["addresses"]["mass_address_probability"][lbl]
        addr = make_address(force_mass)
        director_id = rng.choice(persons_df["id"].tolist())
        companies.append({
            "id": str(uuid.uuid4()),
            "inn": inn_company(),
            "ogrn": ogrn(),
            "name": make_company_name(),
            "status": status,
            "okved_main": okved,
            "reg_date": reg_date.isoformat(),
            "address": addr,
            "director_person_id": director_id,
            "director_changes_last_year": (0 if lbl=="green" else (rng.randint(0,1) if lbl=="yellow" else rng.randint(0,3)))
        })
    companies_df = pd.DataFrame(companies)

    # Ownership
    ownership_rows = []
    company_ids = companies_df["id"].tolist()
    person_ids = persons_df["id"].tolist()

    sanctioned_person_pool = set(random.sample(person_ids, min(cfg["sanctions"]["num_persons"], len(person_ids))))
    sanctioned_company_pool = set()

    owners_choices = cfg["ownership"]["owners_per_company"]
    company_owner_prob = cfg["ownership"]["company_owner_prob"]
    for idx, row in companies_df.iterrows():
        target_id = row["id"]
        lbl = labels[idx]
        owners = []
        owner_count = random.choice(owners_choices[lbl])

        remaining = 100.0
        for j in range(owner_count):
            if j == owner_count - 1:
                share = round(remaining, 2)
            else:
                base = cfg["ownership"].get("share_base_red", 20) if lbl=="red" else cfg["ownership"].get("share_base_non_red", 10)
                share = round(min(remaining - 1, random.randint(base, max(base+10, int(remaining/(owner_count-j)+15)))), 2)
                remaining -= share
            holder_type = "person"
            if idx > 0 and random.random() < company_owner_prob[lbl]:
                holder_type = "company"
            holder_id = random.choice(company_ids[:idx]) if holder_type=="company" and idx>0 else random.choice(person_ids)
            owners.append((holder_type, holder_id, share))
        total = sum(s for _,_,s in owners)
        owners = [(t,h, round(s*100.0/total,2)) for (t,h,s) in owners]
        for t,h,s in owners:
            ownership_rows.append({
                "id": str(uuid.uuid4()),
                "holder_type": t,
                "holder_id": h,
                "target_company_id": target_id,
                "share": s,
                "via": None
            })
    ownership_df = pd.DataFrame(ownership_rows)

    sanctioned_company_candidates = company_ids[: max(10, N//6)]
    sanctioned_company_pool.update(set(random.sample(sanctioned_company_candidates, min(cfg["sanctions"]["num_companies"], len(sanctioned_company_candidates)))))

    # Financials
    fin_rows = []
    years = cfg["financials"]["years"]
    last_year = years[-1]
    for idx, row in companies_df.iterrows():
        cid = row["id"]
        lbl = labels[idx]
        base_rev = float(np.random.lognormal(mean=cfg["financials"]["revenue_lognormal_mean"], sigma=cfg["financials"]["revenue_lognormal_sigma"]))
        if lbl == "green":
            growth = float(np.random.normal(cfg["financials"]["green"]["growth_mean"], cfg["financials"]["green"]["growth_sigma"]))
            margins = [float(np.random.uniform(*cfg["financials"]["green"]["margin_range"])) for _ in years]
            debt_ratio = float(np.random.uniform(*cfg["financials"]["green"]["debt_ratio_range"]))
        elif lbl == "yellow":
            growth = float(np.random.normal(cfg["financials"]["yellow"]["growth_mean"], cfg["financials"]["yellow"]["growth_sigma"]))
            margins = [float(np.random.uniform(*cfg["financials"]["yellow"]["margin_range"])) for _ in years]
            if random.random() < cfg["financials"]["yellow"]["loss_year_prob"]:
                margins[random.randint(0, len(years)-1)] = float(np.random.uniform(*cfg["financials"]["yellow"]["loss_margin_range"]))
            debt_ratio = float(np.random.uniform(*cfg["financials"]["yellow"]["debt_ratio_range"]))
        else:
            growth = float(np.random.normal(cfg["financials"]["red"]["growth_mean"], cfg["financials"]["red"]["growth_sigma"]))
            margins = [float(np.random.uniform(*cfg["financials"]["red"]["margin_range"])) for _ in years]
            debt_ratio = float(np.random.uniform(*cfg["financials"]["red"]["debt_ratio_range"]))
        rev = base_rev
        for y, m in zip(years, margins):
            revenue = max(cfg["financials"]["min_revenue"], rev)
            profit = revenue * m
            assets = max(cfg["financials"]["min_assets"], revenue * float(np.random.uniform(*cfg["financials"]["assets_multiplier_range"])))
            liabilities = max(cfg["financials"]["min_liabilities"], assets * debt_ratio * float(np.random.uniform(*cfg["financials"]["debt_noise_range"])))
            fin_rows.append({
                "company_id": cid, "year": y,
                "revenue": round(float(revenue),2),
                "profit": round(float(profit),2),
                "assets": round(float(assets),2),
                "liabilities": round(float(liabilities),2)
            })
            rev = revenue * (1 + growth)
    financials_df = pd.DataFrame(fin_rows)

    # Courts
    court_rows = []
    for idx, row in companies_df.iterrows():
        cid = row["id"]
        lbl = labels[idx]
        rate = cfg["courts"]["poisson_rate"][lbl]
        case_count = np.random.poisson(rate)
        for _ in range(case_count):
            days_ago = int(random.randint(0, 365*cfg["courts"]["window_years"]))
            filed_at = today - timedelta(days=days_ago)
            amount = float(np.random.lognormal(mean=cfg["courts"]["amount_lognormal_mean"], sigma=cfg["courts"]["amount_lognormal_sigma"]))
            if lbl == "red":
                amount *= float(np.random.uniform(*cfg["courts"]["red_amount_scale"]))
            kind = random.choice(cfg["courts"]["kinds"])
            role = random.choice(cfg["courts"]["roles"])
            status = random.choice(cfg["courts"]["statuses"])
            court_rows.append({
                "id": str(uuid.uuid4()), "company_id": cid, "kind": kind, "role": role,
                "amount": round(float(amount),2), "status": status, "filed_at": filed_at.isoformat()
            })
    court_df = pd.DataFrame(court_rows)

    # Sanctions
    sanctions_rows = []
    for pid in sanctioned_person_pool:
        sanctions_rows.append({
            "id": str(uuid.uuid4()),
            "subject_type": "person",
            "subject_id": pid,
            "list_name": random.choice(cfg["sanctions"]["lists"]),
            "authority": random.choice(cfg["sanctions"]["authorities"]),
            "reason": "Synthetic listing",
            "date_added": (today - timedelta(days=int(random.randint(30, 900)))).isoformat()
        })
    for cid in sanctioned_company_pool:
        sanctions_rows.append({
            "id": str(uuid.uuid4()),
            "subject_type": "company",
            "subject_id": cid,
            "list_name": random.choice(cfg["sanctions"]["lists"]),
            "authority": random.choice(cfg["sanctions"]["authorities"]),
            "reason": "Synthetic listing",
            "date_added": (today - timedelta(days=int(random.randint(30, 1200)))).isoformat()
        })
    sanctions_df = pd.DataFrame(sanctions_rows)

    # Inject critical compliance to subset of red
    red_ids = companies_df.index.tolist()  # indices, to map to labels
    red_company_ids = [companies_df.iloc[i]["id"] for i in range(N) if labels[i]=="red"]
    frac_crit = cfg["ownership"]["sanction_inject"]["fraction_red_companies_critical"]
    inject_share = cfg["ownership"]["sanction_inject"]["share_for_injected_owner"]
    target_n = max(1, int(len(red_company_ids) * frac_crit))
    sel = random.sample(red_company_ids, min(target_n, len(red_company_ids)))
    for cid in sel:
        mask = (ownership_df["target_company_id"] == cid)
        old = ownership_df[mask].copy()
        total = old["share"].sum()
        if total > 0:
            ownership_df.loc[mask, "share"] = old["share"] * (100.0 - inject_share) / total
        # Prefer sanctioned person
        if len(sanctioned_person_pool) > 0 and random.random() < 0.6:
            holder_type = "person"; holder_id = random.choice(list(sanctioned_person_pool))
        else:
            holder_type = "company"
            if len(sanctioned_company_pool) == 0:
                holder_id = companies_df["id"].iloc[0]
                sanctioned_company_pool.add(holder_id)
                sanctions_df = pd.concat([sanctions_df, pd.DataFrame([{
                    "id": str(uuid.uuid4()), "subject_type": "company", "subject_id": holder_id,
                    "list_name": random.choice(cfg["sanctions"]["lists"]),
                    "authority": random.choice(cfg["sanctions"]["authorities"]),
                    "reason": "Synthetic listing",
                    "date_added": (today - timedelta(days=int(random.randint(60, 800)))).isoformat()
                }])], ignore_index=True)
            else:
                holder_id = random.choice(list(sanctioned_company_pool))
        ownership_df = pd.concat([ownership_df, pd.DataFrame([{
            "id": str(uuid.uuid4()),
            "holder_type": holder_type,
            "holder_id": holder_id,
            "target_company_id": cid,
            "share": inject_share,
            "via": None
        }])], ignore_index=True)

    # Mass address flag
    addr_counts = companies_df["address"].value_counts().to_dict()
    threshold = cfg["addresses"]["mass_address_threshold"]
    companies_df["mass_address"] = companies_df["address"].map(lambda a: addr_counts.get(a,0) >= threshold)

    params = {
        "financials": {"last_year": cfg["financials"]["years"][-1]},
        "risk": cfg["risk"],
        "grade_rules": cfg["grade_rules"]
    }
    scores_df = compute_scores(companies_df, financials_df, court_df, ownership_df, sanctions_df, today, params)

    # Due diligence synthesis
    dd_cfg = cfg.get("due_diligence", {})
    assets_threshold = dd_cfg.get("assets_threshold", 0)
    blocked_bank_choices = dd_cfg.get("blocked_banks", [])
    gov_cfg = dd_cfg.get("gov_contracts", {})
    gov_lambda = gov_cfg.get("poisson_lambda", {lbl: 0 for lbl in ["green","yellow","red"]})
    gov_amount_range = gov_cfg.get("amount_range", {lbl: [0, 0] for lbl in ["green","yellow","red"]})
    quality_docs_options = dd_cfg.get("quality_docs_options", [
        "Паспорт качества",
        "Сертификат соответствия ГОСТ",
        "Добровольная сертификация ТР ТС",
        "Свидетельство СРО"
    ])
    regulatory_violation_examples = dd_cfg.get("regulatory_violation_examples", [
        "Нарушение требований пожарной безопасности",
        "Нарушение охраны труда",
        "Несоблюдение экологических норм"
    ])

    dd_rows = []
    for idx, row in companies_df.iterrows():
        lbl = labels[idx]
        cid = row["id"]
        reg_date = datetime.fromisoformat(row["reg_date"]).date()
        age_years = max(0, int((today - reg_date).days // 365))

        fin_latest = financials_df[financials_df["company_id"] == cid].sort_values("year").tail(1)
        assets_value = float(fin_latest["assets"].iloc[0]) if not fin_latest.empty else 0.0

        staff_range = dd_cfg.get("staff_count_range", {}).get(lbl, [5, 25])
        staff_count = rng.randint(int(staff_range[0]), int(staff_range[1])) if staff_range[1] >= staff_range[0] else int(staff_range[0])

        gov_lam = gov_lambda.get(lbl, 0.0)
        gov_count = int(max(0, np.random.poisson(gov_lam))) if gov_lam > 0 else 0
        amt_low, amt_high = gov_amount_range.get(lbl, [0, 0])
        if gov_count > 0 and amt_high > amt_low:
            gov_total = float(sum(rng.uniform(amt_low, amt_high) for _ in range(gov_count)))
        elif gov_count > 0:
            gov_total = float(gov_count * amt_low)
        else:
            gov_total = 0.0

        if not court_df.empty:
            company_courts = court_df[court_df["company_id"] == cid]
            active_courts = any(st != "Завершено" for st in company_courts["status"]) if not company_courts.empty else False
        else:
            active_courts = False

        blocked_accounts = rng.random() < dd_cfg.get("blocked_accounts_prob", {}).get(lbl, 0.0)
        if blocked_accounts and blocked_bank_choices:
            sample_size = min(len(blocked_bank_choices), rng.randint(1, min(2, len(blocked_bank_choices))))
            blocked_banks = ", ".join(rng.sample(blocked_bank_choices, sample_size))
        else:
            blocked_banks = ""

        quality_docs_list = []
        if rng.random() < dd_cfg.get("quality_docs_prob", {}).get(lbl, 0.0):
            sample_size = min(len(quality_docs_options), rng.randint(1, max(1, len(quality_docs_options))))
            quality_docs_list = rng.sample(quality_docs_options, sample_size)

        regulatory_details = ""
        has_regulatory_flags = rng.random() < dd_cfg.get("regulatory_violations_prob", {}).get(lbl, 0.0)
        if has_regulatory_flags and regulatory_violation_examples:
            sample_size = min(len(regulatory_violation_examples), rng.randint(1, max(1, len(regulatory_violation_examples))))
            regulatory_details = "; ".join(rng.sample(regulatory_violation_examples, sample_size))

        has_quality_docs_flag = len(quality_docs_list) > 0

        dd_rows.append({
            "company_id": cid,
            "egrul_has_invalid_data": rng.random() < dd_cfg.get("egrul_invalid_prob", {}).get(lbl, 0.0),
            "status_issue": row["status"] in {"LIQUIDATION", "BANKRUPTCY", "REORGANIZATION", "ADDRESS_CHANGE"},
            "identity_matches": rng.random() >= dd_cfg.get("identity_mismatch_prob", {}).get(lbl, 0.0),
            "age_years": age_years,
            "staff_count": staff_count,
            "staff_sufficient": rng.random() < dd_cfg.get("staff_sufficiency_prob", {}).get(lbl, 0.0),
            "has_quality_docs": has_quality_docs_flag,
            "quality_docs_details": ", ".join(quality_docs_list),
            "has_assets": assets_value >= assets_threshold,
            "assets_total_value": round(float(assets_value), 2),
            "tax_debt": rng.random() < dd_cfg.get("tax_debt_prob", {}).get(lbl, 0.0),
            "fssp_debt": rng.random() < dd_cfg.get("fssp_debt_prob", {}).get(lbl, 0.0),
            "open_credit_lines": rng.random() < dd_cfg.get("open_credit_prob", {}).get(lbl, 0.0),
            "has_leasing": rng.random() < dd_cfg.get("leasing_prob", {}).get(lbl, 0.0),
            "active_court_cases": active_courts,
            "executive_debt": rng.random() < dd_cfg.get("executive_debt_prob", {}).get(lbl, 0.0),
            "gov_contracts_count": gov_count,
            "gov_contracts_total": round(gov_total, 2),
            "in_rnp": rng.random() < dd_cfg.get("in_rnp_prob", {}).get(lbl, 0.0),
            "mass_registration": bool(row.get("mass_address", False)),
            "director_disqualified": rng.random() < dd_cfg.get("director_disqualified_prob", {}).get(lbl, 0.0),
            "director_nominee": rng.random() < dd_cfg.get("director_nominee_prob", {}).get(lbl, 0.0),
            "has_power_of_attorney": rng.random() < dd_cfg.get("attorney_prob", {}).get(lbl, 0.0),
            "blocked_accounts": blocked_accounts,
            "blocked_banks": blocked_banks,
            "tax_clearance_recent": rng.random() < dd_cfg.get("tax_clearance_prob", {}).get(lbl, 0.0),
            "regulatory_violations": has_regulatory_flags,
            "regulatory_violations_details": regulatory_details
        })

    due_diligence_df = pd.DataFrame(dd_rows)

    return {
        "companies": companies_df,
        "persons": persons_df,
        "ownership": ownership_df,
        "financials": financials_df,
        "court_cases": court_df,
        "sanctions": sanctions_df,
        "risk_scores": scores_df,
        "due_diligence": due_diligence_df
    }
