# from __future__ import annotations

# import pandas as pd
# from typing import Dict, Any, List


# # Canonical column names we normalize into
# MONTH_COL = "month"
# TOTAL_EXP_COL = "total_expenditure"
# INCOME_COL = "income"
# EMI_COL = "emi_loans"
# SAVINGS_COL = "savings"


# def _norm(s: str) -> str:
#     """Normalize a column name for matching."""
#     return (
#         str(s)
#         .strip()
#         .lower()
#         .replace("₹", "")
#         .replace("$", "")
#         .replace("%", "")
#         .replace("/", "_")
#         .replace("-", "_")
#         .replace("(", "")
#         .replace(")", "")
#         .replace(" ", "_")
#         .replace("__", "_")
#     )


# def _pick_col(df: pd.DataFrame, candidates: List[str]) -> str | None:
#     """Pick the first matching column from candidates using normalized comparison."""
#     norm_map = {_norm(c): c for c in df.columns}
#     for cand in candidates:
#         key = _norm(cand)
#         if key in norm_map:
#             return norm_map[key]
#     return None


# def _load_monthly(csv_path: str) -> pd.DataFrame:
#     df = pd.read_csv(csv_path)

#     # Detect required columns from common naming variants
#     month_src = _pick_col(df, ["Month", "month", "Date", "date"])
#     income_src = _pick_col(df, ["Income (₹)", "Income", "income", "Monthly_Income", "monthly_income"])
#     total_src = _pick_col(
#         df,
#         [
#             "Total Expenditure (₹)",
#             "Total_Expenditure",
#             "Total Expenditure",
#             "total_expenditure",
#             "Total_Spending",
#             "total_spending",
#         ],
#     )

#     # Optional columns
#     emi_src = _pick_col(df, ["EMI/Loans (₹)", "EMI_Loans", "EMI/Loans", "emi_loans", "Loans", "loans"])
#     savings_src = _pick_col(df, ["Savings (₹)", "Savings", "savings"])

#     missing = []
#     if not month_src:
#         missing.append("Month/Date")
#     if not income_src:
#         missing.append("Income")
#     if not total_src:
#         missing.append("Total Expenditure")
#     if missing:
#         raise ValueError(
#             f"CSV missing required columns: {missing}. Found columns: {list(df.columns)}"
#         )

#     # Rename to canonical names
#     rename_map = {
#         month_src: MONTH_COL,
#         income_src: INCOME_COL,
#         total_src: TOTAL_EXP_COL,
#     }
#     if emi_src:
#         rename_map[emi_src] = EMI_COL
#     if savings_src:
#         rename_map[savings_src] = SAVINGS_COL

#     df = df.rename(columns=rename_map)

#     # Parse month/date
#     df[MONTH_COL] = pd.to_datetime(df[MONTH_COL], errors="coerce")
#     df = df.dropna(subset=[MONTH_COL]).sort_values(MONTH_COL).reset_index(drop=True)

#     # Convert numeric cols
#     for c in df.columns:
#         if c != MONTH_COL:
#             df[c] = pd.to_numeric(df[c], errors="coerce")

#     return df


# def _pct_change(curr: float, prev: float) -> float | None:
#     if prev is None or prev == 0 or pd.isna(prev):
#         return None
#     return round(((curr - prev) / prev) * 100, 1)


# def trend_analysis(csv_path: str) -> Dict[str, Any]:
#     df = _load_monthly(csv_path)
#     last = df.iloc[-1]
#     prev = df.iloc[-2] if len(df) >= 2 else None

#     total_exp = float(last[TOTAL_EXP_COL])
#     income = float(last[INCOME_COL])

#     mom_change = None
#     if prev is not None and not pd.isna(prev[TOTAL_EXP_COL]):
#         mom_change = _pct_change(total_exp, float(prev[TOTAL_EXP_COL]))

#     # Dynamically detect category columns (everything except known fields)
#     category_cols = [
#         c
#         for c in df.columns
#         if c not in {MONTH_COL, INCOME_COL, TOTAL_EXP_COL, EMI_COL, SAVINGS_COL}
#     ]

#     top_categories: Dict[str, float] = {}
#     if category_cols:
#         last_cats = last[category_cols].dropna().sort_values(ascending=False)
#         for k, v in last_cats.head(3).items():
#             top_categories[str(k)] = round(float(v), 2)

#     expense_ratio_pct = round((total_exp / income) * 100, 1) if income else None

#     return {
#         "month": str(last[MONTH_COL].date()),
#         "total_expenditure": round(total_exp, 2),
#         "income": round(income, 2),
#         "expense_ratio_pct": expense_ratio_pct,
#         "month_over_month_spend_change_pct": mom_change,
#         "top_categories_latest_month": top_categories,
#     }


# def risk_estimation(csv_path: str) -> Dict[str, Any]:
#     df = _load_monthly(csv_path)
#     last = df.iloc[-1]

#     total_exp = float(last[TOTAL_EXP_COL])
#     income = float(last[INCOME_COL]) if not pd.isna(last[INCOME_COL]) else 0.0

#     expense_ratio = (total_exp / income) if income else 999.0

#     #emi = float(last[EMI_COL]) if EMI_COL in df.columns and not pd.isna(last.get(EMI_COL)) else 0.0
#     emi = 0.0
#     if EMI_COL in df.columns:
#         val = last.get(EMI_COL)
#         if val is not None and not pd.isna(val):
#             emi = float(val)
#     emi_ratio = (emi / income) if income else 0.0

#     anomalies: List[dict] = []

#     # MoM total spend spike
#     if len(df) >= 2:
#         prev_total = float(df.iloc[-2][TOTAL_EXP_COL])
#         change = _pct_change(total_exp, prev_total)
#         if change is not None and change >= 20:
#             anomalies.append(
#                 {
#                     "type": "monthly_spend_spike",
#                     "month": str(last[MONTH_COL].date()),
#                     "value": round(total_exp, 2),
#                     "change_pct": change,
#                     "reason": "Total expenditure increased sharply vs previous month.",
#                 }
#             )

#     # "High vs last 12 months" spike (helps surface anomalies even when MoM is calm)
#     window = df.tail(13)  # 12 months + current
#     if len(window) >= 2:
#         prev12 = window.iloc[:-1]
#         prev12_max = float(prev12[TOTAL_EXP_COL].max())
#         if prev12_max > 0 and total_exp >= 1.15 * prev12_max:
#             anomalies.append({
#                 "type": "spend_high_vs_12m",
#                 "month": str(last[MONTH_COL].date()),
#                 "value": round(total_exp, 2),
#                 "prev12m_max": round(prev12_max, 2),
#                 "reason": "Total expenditure is unusually high compared to the last 12 months.",
#             })

#     # Category spike vs last 6 months baseline
#     category_cols = [
#         c
#         for c in df.columns
#         if c not in {MONTH_COL, INCOME_COL, TOTAL_EXP_COL, EMI_COL, SAVINGS_COL}
#     ]
#     tail = df.tail(7)  # baseline previous 6 + current
#     if category_cols and len(tail) >= 2:
#         baseline = tail.iloc[:-1]
#         for cat in category_cols:
#             base_avg = float(baseline[cat].mean(skipna=True))
#             curr = float(last[cat]) if not pd.isna(last[cat]) else 0.0
#             # spike: 1.5x baseline AND meaningful absolute delta
#             if base_avg > 0 and curr >= 1.5 * base_avg and (curr - base_avg) >= 500:
#                 anomalies.append(
#                     {
#                         "type": "category_spike",
#                         "month": str(last[MONTH_COL].date()),
#                         "category": str(cat),
#                         "value": round(curr, 2),
#                         "baseline_avg_6m": round(base_avg, 2),
#                         "reason": "Category spending is significantly higher than recent baseline.",
#                     }
#                 )

#     cashflow_risk = total_exp > income if income else True
#     high_emi_burden = emi_ratio >= 0.30

#     risk_level = "low"
#     if cashflow_risk or expense_ratio >= 0.85 or high_emi_burden or len(anomalies) >= 2:
#         risk_level = "medium"
#     if (expense_ratio >= 1.0) or (cashflow_risk and high_emi_burden) or len(anomalies) >= 4:
#         risk_level = "high"

#     return {
#         "month": str(last[MONTH_COL].date()),
#         "risk_level": risk_level,
#         "cashflow_risk": bool(cashflow_risk),
#         "expense_ratio_pct": round(expense_ratio * 100, 1) if income else None,
#         "anomalies": anomalies[:8],
#         "emi_amount_latest_month": round(emi, 2),
#         "emi_ratio_pct_latest_month": round(emi_ratio * 100, 1) if income else None,
#         "emi_note": "EMI/loan payment shown is for the latest month only. Do not infer overall debt status from this value.",
#     }


# def financial_insights(csv_path: str) -> Dict[str, Any]:
#     df = _load_monthly(csv_path)
#     last = df.iloc[-1]

#     income = float(last[INCOME_COL]) if not pd.isna(last[INCOME_COL]) else 0.0
#     total_exp = float(last[TOTAL_EXP_COL]) if not pd.isna(last[TOTAL_EXP_COL]) else 0.0

#     emi = float(last[EMI_COL]) if EMI_COL in df.columns and not pd.isna(last.get(EMI_COL)) else 0.0
#     savings = float(last[SAVINGS_COL]) if SAVINGS_COL in df.columns and not pd.isna(last.get(SAVINGS_COL)) else 0.0

#     emi_ratio = (emi / income) if income else 0.0
#     savings_ratio = (savings / income) if income else 0.0

#     # Conservative proxy for "interest savings"
#     est_interest_savings = 0.0
#     if emi > 0 and emi_ratio >= 0.25:
#         est_interest_savings = round(emi * 0.05, 2)  # 5% of EMI as proxy

#     recs: List[str] = []

#     if income:
#         recs.append(
#             f"Expense-to-income ratio is ~{round((total_exp / income) * 100, 1)}%. Targeting <80% improves stability."
#         )
#     if emi_ratio >= 0.30:
#         recs.append(
#             "EMI/Loans are a high portion of income. Consider prepaying principal or refinancing to reduce interest burden."
#         )
#     elif emi > 0:
#         recs.append(
#             "If you have multiple loans/cards, prioritize highest-interest debt first (avalanche method)."
#         )

#     if SAVINGS_COL in df.columns and income:
#         if savings_ratio < 0.10:
#             recs.append(
#                 "Savings rate looks low. Automate a fixed transfer to savings right after income is received."
#             )
#         else:
#             recs.append(f"Savings rate is ~{round(savings_ratio*100,1)}%. Keep it consistent month-to-month.")

#     # Add a discretionary spending note if present
#     for candidate in ["Shopping & Wants (₹)", "Shopping", "Shopping_&_Wants", "shopping", "shopping_wants"]:
#         if candidate in df.columns:
#             val = float(last[candidate]) if not pd.isna(last[candidate]) else 0.0
#             recs.append(f"{candidate}: {round(val,2)}. Setting a cap can reduce discretionary spending swings.")
#             break

#     return {
#         "month": str(last[MONTH_COL].date()),
#         "estimated_interest_savings": float(est_interest_savings),
#         "key_recommendations": recs[:5],
#     }


# def proactive_check(csv_path: str) -> Dict[str, Any]:
#     t = trend_analysis(csv_path)
#     r = risk_estimation(csv_path)
#     f = financial_insights(csv_path)

#     highlights: List[str] = []
#     highlights.append(f"Month: {t['month']} | Spending: {t['total_expenditure']:.0f} | Income: {t['income']:.0f}")
#     if t["month_over_month_spend_change_pct"] is not None:
#         highlights.append(f"MoM spending change: {t['month_over_month_spend_change_pct']}%")
#     if t["expense_ratio_pct"] is not None:
#         highlights.append(f"Expense ratio: {t['expense_ratio_pct']}%")
#     highlights.append(f"Risk level: {r['risk_level']} (cashflow risk: {r['cashflow_risk']})")

#     if t["top_categories_latest_month"]:
#         top = next(iter(t["top_categories_latest_month"].items()))
#         highlights.append(f"Top category (latest month): {top[0]} ({top[1]:.0f})")

   
#     if r["anomalies"]:
#         a = r["anomalies"][0]

#         if a["type"] == "monthly_spend_spike":
#             highlights.append(f"Anomaly: total spend spike ({a['change_pct']}%)")

#         elif a["type"] == "spend_high_vs_12m":
#             highlights.append("Anomaly: spending unusually high compared to last 12 months")

#         else:
#             highlights.append(f"Anomaly: {a.get('category','Category')} spike vs baseline")
#     if f["estimated_interest_savings"] > 0:
#         highlights.append(f"Potential interest savings estimate: ~{f['estimated_interest_savings']:.0f}/month (proxy)")

#     return {
#         "summary": "Proactive scan completed: identified trends, risk signals, and savings opportunities.",
#         "highlights": highlights[:6],
#     }


from __future__ import annotations

import pandas as pd
from typing import Dict, Any, List


# Canonical column names we normalize into
MONTH_COL = "month"
TOTAL_EXP_COL = "total_expenditure"
INCOME_COL = "income"
EMI_COL = "emi_loans"
SAVINGS_COL = "savings"


def _norm(s: str) -> str:
    """Normalize a column name for matching."""
    return (
        str(s)
        .strip()
        .lower()
        .replace("₹", "")
        .replace("$", "")
        .replace("%", "")
        .replace("/", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "_")
        .replace("__", "_")
    )


def _pick_col(df: pd.DataFrame, candidates: List[str]) -> str | None:
    """Pick the first matching column from candidates using normalized comparison."""
    norm_map = {_norm(c): c for c in df.columns}
    for cand in candidates:
        key = _norm(cand)
        if key in norm_map:
            return norm_map[key]
    return None


def _load_monthly(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # Detect required columns from common naming variants
    month_src = _pick_col(df, ["Month", "month", "Date", "date"])
    income_src = _pick_col(df, ["Income (₹)", "Income", "income", "Monthly_Income", "monthly_income"])
    total_src = _pick_col(
        df,
        [
            "Total Expenditure (₹)",
            "Total_Expenditure",
            "Total Expenditure",
            "total_expenditure",
            "Total_Spending",
            "total_spending",
        ],
    )

    # Optional columns
    emi_src = _pick_col(df, ["EMI/Loans (₹)", "EMI_Loans", "EMI/Loans", "emi_loans", "Loans", "loans"])
    savings_src = _pick_col(df, ["Savings (₹)", "Savings", "savings"])

    missing = []
    if not month_src:
        missing.append("Month/Date")
    if not income_src:
        missing.append("Income")
    if not total_src:
        missing.append("Total Expenditure")
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}. Found columns: {list(df.columns)}")

    # Rename to canonical names
    rename_map = {
        month_src: MONTH_COL,
        income_src: INCOME_COL,
        total_src: TOTAL_EXP_COL,
    }
    if emi_src:
        rename_map[emi_src] = EMI_COL
    if savings_src:
        rename_map[savings_src] = SAVINGS_COL

    df = df.rename(columns=rename_map)

    # Parse month/date
    df[MONTH_COL] = pd.to_datetime(df[MONTH_COL], errors="coerce")
    df = df.dropna(subset=[MONTH_COL]).sort_values(MONTH_COL).reset_index(drop=True)

    # Convert numeric cols
    for c in df.columns:
        if c != MONTH_COL:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def _pct_change(curr: float, prev: float) -> float | None:
    if prev is None or prev == 0 or pd.isna(prev):
        return None
    return round(((curr - prev) / prev) * 100, 1)


def _safe_float(x: Any, default: float = 0.0) -> float:
    if x is None or pd.isna(x):
        return default
    try:
        return float(x)
    except Exception:
        return default


def calculate_financial_health_score(metrics: Dict[str, float]) -> int:
    score = 100

    expense_ratio = float(metrics.get("expense_ratio", 0.0))
    savings_rate = float(metrics.get("savings_rate", 0.0))
    emi_ratio = float(metrics.get("emi_ratio", 0.0))

    if expense_ratio > 0.8:
        score -= 25
    elif expense_ratio > 0.7:
        score -= 15

    if savings_rate < 0.1:
        score -= 20
    elif savings_rate < 0.2:
        score -= 10

    if emi_ratio > 0.4:
        score -= 20
    elif emi_ratio > 0.3:
        score -= 10

    return max(score, 0)


def trend_analysis(csv_path: str) -> Dict[str, Any]:
    df = _load_monthly(csv_path)
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else None

    total_exp = _safe_float(last.get(TOTAL_EXP_COL))
    income = _safe_float(last.get(INCOME_COL))

    emi = _safe_float(last.get(EMI_COL), default=0.0) if EMI_COL in df.columns else 0.0

    savings_val = None
    if SAVINGS_COL in df.columns and not pd.isna(last.get(SAVINGS_COL)):
        savings_val = _safe_float(last.get(SAVINGS_COL), default=0.0)
    else:
        if income or total_exp or emi:
            savings_val = float(income - total_exp - emi)

    expense_ratio = (total_exp / income) if income else 0.0
    savings_rate = (savings_val / income) if (income and savings_val is not None) else 0.0
    emi_ratio = (emi / income) if income else 0.0

    metrics = {
        "expense_ratio": float(expense_ratio),
        "savings_rate": float(savings_rate),
        "emi_ratio": float(emi_ratio),
    }
    health_score = calculate_financial_health_score(metrics)

    mom_change = None
    if prev is not None and not pd.isna(prev[TOTAL_EXP_COL]):
        mom_change = _pct_change(total_exp, _safe_float(prev.get(TOTAL_EXP_COL)))

    # Dynamically detect category columns (everything except known fields)
    category_cols = [
        c
        for c in df.columns
        if c not in {MONTH_COL, INCOME_COL, TOTAL_EXP_COL, EMI_COL, SAVINGS_COL}
    ]

    top_categories: Dict[str, float] = {}
    if category_cols:
        last_cats = last[category_cols].dropna().sort_values(ascending=False)
        for k, v in last_cats.head(3).items():
            top_categories[str(k)] = round(_safe_float(v), 2)

    expense_ratio_pct = round((total_exp / income) * 100, 1) if income else None

    return {
        "month": str(last[MONTH_COL].date()),
        "total_expenditure": round(total_exp, 2),
        "income": round(income, 2),
        "total_expenditure_latest_month": round(total_exp, 2),
        "income_latest_month": round(income, 2),
        "expense_ratio": round(expense_ratio, 4),
        "savings_rate": round(savings_rate, 4),
        "emi_ratio": round(emi_ratio, 4),
        "health_score": int(health_score),
        "expense_ratio_pct": expense_ratio_pct,
        "month_over_month_spend_change_pct": mom_change,
        "month_over_month_change": mom_change,
        "top_categories_latest_month": top_categories,
        "top_spending_categories": top_categories,
    }


def risk_estimation(csv_path: str) -> Dict[str, Any]:
    df = _load_monthly(csv_path)
    last = df.iloc[-1]

    total_exp = _safe_float(last.get(TOTAL_EXP_COL))
    income = _safe_float(last.get(INCOME_COL), default=0.0)

    expense_ratio = (total_exp / income) if income else 999.0

    emi = 0.0
    if EMI_COL in df.columns:
        emi = _safe_float(last.get(EMI_COL), default=0.0)

    emi_ratio = (emi / income) if income else 0.0

    savings_val = None
    if SAVINGS_COL in df.columns and not pd.isna(last.get(SAVINGS_COL)):
        savings_val = _safe_float(last.get(SAVINGS_COL), default=0.0)
    else:
        if income or total_exp or emi:
            savings_val = float(income - total_exp - emi)

    savings_rate = (savings_val / income) if (income and savings_val is not None) else 0.0

    metrics = {
        "expense_ratio": float(expense_ratio),
        "savings_rate": float(savings_rate),
        "emi_ratio": float(emi_ratio),
    }
    health_score = calculate_financial_health_score(metrics)

    anomalies: List[dict] = []

    # MoM total spend spike
    if len(df) >= 2:
        prev_total = _safe_float(df.iloc[-2].get(TOTAL_EXP_COL))
        change = _pct_change(total_exp, prev_total)
        if change is not None and change >= 20:
            anomalies.append(
                {
                    "type": "monthly_spend_spike",
                    "month": str(last[MONTH_COL].date()),
                    "value": round(total_exp, 2),
                    "change_pct": change,
                    "reason": "Total expenditure increased sharply vs previous month.",
                }
            )

    # "High vs last 12 months" spike
    window = df.tail(13)  # 12 months + current
    if len(window) >= 2:
        prev12 = window.iloc[:-1]
        prev12_max = _safe_float(prev12[TOTAL_EXP_COL].max())
        if prev12_max > 0 and total_exp >= 1.15 * prev12_max:
            anomalies.append(
                {
                    "type": "spend_high_vs_12m",
                    "month": str(last[MONTH_COL].date()),
                    "value": round(total_exp, 2),
                    "prev12m_max": round(prev12_max, 2),
                    "reason": "Total expenditure is unusually high compared to the last 12 months.",
                }
            )

    # Category spike vs last 6 months baseline
    category_cols = [
        c
        for c in df.columns
        if c not in {MONTH_COL, INCOME_COL, TOTAL_EXP_COL, EMI_COL, SAVINGS_COL}
    ]
    tail = df.tail(7)  # baseline previous 6 + current
    if category_cols and len(tail) >= 2:
        baseline = tail.iloc[:-1]
        for cat in category_cols:
            base_avg = _safe_float(baseline[cat].mean(skipna=True))
            curr = _safe_float(last.get(cat), default=0.0)
            # spike: 1.5x baseline AND meaningful absolute delta
            if base_avg > 0 and curr >= 1.5 * base_avg and (curr - base_avg) >= 500:
                anomalies.append(
                    {
                        "type": "category_spike",
                        "month": str(last[MONTH_COL].date()),
                        "category": str(cat),
                        "value": round(curr, 2),
                        "baseline_avg_6m": round(base_avg, 2),
                        "reason": "Category spending is significantly higher than recent baseline.",
                    }
                )

    cashflow_risk = total_exp > income if income else True
    high_emi_burden = emi_ratio >= 0.30

    risk_level = "low"
    if cashflow_risk or expense_ratio >= 0.85 or high_emi_burden or len(anomalies) >= 2:
        risk_level = "medium"
    if (expense_ratio >= 1.0) or (cashflow_risk and high_emi_burden) or len(anomalies) >= 4:
        risk_level = "high"

    return {
        "month": str(last[MONTH_COL].date()),
        "risk_level": risk_level,
        "cashflow_risk": bool(cashflow_risk),
        "expense_ratio": round(expense_ratio, 4),
        "savings_rate": round(savings_rate, 4),
        "emi_ratio": round(emi_ratio, 4),
        "health_score": int(health_score),
        "expense_ratio_pct": round(expense_ratio * 100, 1) if income else None,
        "anomalies": anomalies[:8],
        "emi_amount_latest_month": round(emi, 2),
        "emi_ratio_pct_latest_month": round(emi_ratio * 100, 1) if income else None,
        "emi_note": "EMI/loan payment shown is for the latest month only. Do not infer overall debt status from this value.",
    }


def financial_insights(csv_path: str) -> Dict[str, Any]:
    df = _load_monthly(csv_path)
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else None

    notes: List[str] = []

    income = _safe_float(last.get(INCOME_COL), default=0.0)
    total_exp = _safe_float(last.get(TOTAL_EXP_COL), default=0.0)

    # EMI (optional)
    emi = _safe_float(last.get(EMI_COL), default=0.0) if EMI_COL in df.columns else 0.0
    emi_ratio = (emi / income) if income else 0.0

    # Savings: prefer explicit column; otherwise compute
    savings_source = "missing"
    savings_val: float | None = None

    if SAVINGS_COL in df.columns and not pd.isna(last.get(SAVINGS_COL)):
        savings_val = _safe_float(last.get(SAVINGS_COL), default=0.0)
        savings_source = "column"
    else:
        # computed savings = income - expenditure - emi (if emi exists)
        if income or total_exp or emi:
            savings_val = float(income - total_exp - emi)
            savings_source = "computed"
            notes.append("Savings was computed as income - total_expenditure - emi (because savings column was missing/empty).")

    savings_ratio_pct = round((savings_val / income) * 100, 1) if (income and savings_val is not None) else None

    # MoM savings change (only if we can compute prev savings)
    savings_change_amount = None
    savings_change_pct = None
    if prev is not None and savings_val is not None:
        prev_income = _safe_float(prev.get(INCOME_COL), default=0.0)
        prev_total = _safe_float(prev.get(TOTAL_EXP_COL), default=0.0)
        prev_emi = _safe_float(prev.get(EMI_COL), default=0.0) if EMI_COL in df.columns else 0.0

        if SAVINGS_COL in df.columns and not pd.isna(prev.get(SAVINGS_COL)):
            prev_savings = _safe_float(prev.get(SAVINGS_COL), default=0.0)
        else:
            prev_savings = float(prev_income - prev_total - prev_emi)

        savings_change_amount = round(float(savings_val - prev_savings), 2)
        savings_change_pct = _pct_change(float(savings_val), float(prev_savings))

    # Conservative proxy for "interest savings"
    est_interest_savings = 0.0
    if emi > 0 and emi_ratio >= 0.25:
        est_interest_savings = round(emi * 0.05, 2)  # 5% of EMI as proxy

    recs: List[str] = []

    if income:
        recs.append(
            f"Expense-to-income ratio is ~{round((total_exp / income) * 100, 1)}%. Targeting <80% improves stability."
        )

    # EMI messaging safety
    if emi == 0:
        recs.append("No EMI payment recorded in the latest month.")
    elif emi_ratio >= 0.30:
        recs.append(
            "EMI/Loans are a high portion of income. Consider prepaying principal or refinancing to reduce interest burden."
        )
    else:
        recs.append("If you have multiple loans/cards, prioritize highest-interest debt first (avalanche method).")

    # Savings recommendations
    if savings_val is not None and income:
        if savings_ratio_pct is not None and savings_ratio_pct < 10:
            recs.append("Savings rate looks low. Automate a fixed transfer to savings right after income is received.")
        elif savings_ratio_pct is not None:
            recs.append(f"Savings rate is ~{savings_ratio_pct}%. Keep it consistent month-to-month.")
    elif income:
        notes.append("Could not compute savings rate due to missing values.")

    # Discretionary spending note (match by normalized names, not raw)
    # We scan current df columns (already canonical/renamed) and match common variants
    discretionary_src = _pick_col(
        df,
        [
            "shopping_wants",
            "shopping",
            "wants",
            "discretionary",
            "entertainment",
            "dining_out",
            "eating_out",
        ],
    )
    if discretionary_src and discretionary_src in df.columns:
        val = _safe_float(last.get(discretionary_src), default=0.0)
        recs.append(f"{discretionary_src}: {round(val, 2)}. Setting a cap can reduce discretionary spending swings.")

    return {
        "month": str(last[MONTH_COL].date()),
        "latest_income": round(income, 2),
        "latest_total_expenditure": round(total_exp, 2),
        "latest_emi_amount": round(emi, 2),
        "emi_ratio_pct_latest_month": round(emi_ratio * 100, 1) if income else None,
        "latest_savings_amount": round(savings_val, 2) if savings_val is not None else None,
        "savings_rate_pct_latest_month": savings_ratio_pct,
        "savings_source": savings_source,  # "column" or "computed" or "missing"
        "savings_change_amount_mom": savings_change_amount,
        "savings_change_pct_mom": savings_change_pct,
        "estimated_interest_savings": float(est_interest_savings),
        "key_recommendations": recs[:6],
        "notes": notes[:4],
    }


def proactive_check(csv_path: str) -> Dict[str, Any]:
    t = trend_analysis(csv_path)
    r = risk_estimation(csv_path)
    f = financial_insights(csv_path)

    highlights: List[str] = []
    highlights.append(f"Month: {t['month']} | Spending: {t['total_expenditure']:.0f} | Income: {t['income']:.0f}")
    if t["month_over_month_spend_change_pct"] is not None:
        highlights.append(f"MoM spending change: {t['month_over_month_spend_change_pct']}%")
    if t["expense_ratio_pct"] is not None:
        highlights.append(f"Expense ratio: {t['expense_ratio_pct']}%")
    highlights.append(f"Risk level: {r['risk_level']} (cashflow risk: {r['cashflow_risk']})")

    if t["top_categories_latest_month"]:
        top = next(iter(t["top_categories_latest_month"].items()))
        highlights.append(f"Top category (latest month): {top[0]} ({top[1]:.0f})")

    if r["anomalies"]:
        a = r["anomalies"][0]
        if a["type"] == "monthly_spend_spike":
            highlights.append(f"Anomaly: total spend spike ({a['change_pct']}%)")
        elif a["type"] == "spend_high_vs_12m":
            highlights.append("Anomaly: spending unusually high compared to last 12 months")
        else:
            highlights.append(f"Anomaly: {a.get('category','Category')} spike vs baseline")

    if f.get("estimated_interest_savings", 0) > 0:
        highlights.append(f"Potential interest savings estimate: ~{f['estimated_interest_savings']:.0f}/month (proxy)")

    # savings highlight (new)
    if f.get("latest_savings_amount") is not None:
        highlights.append(f"Latest savings: {f['latest_savings_amount']:.0f} ({f.get('savings_source','')})")

    return {
        "summary": "Proactive scan completed: identified trends, risk signals, and savings opportunities.",
        "highlights": highlights[:6],
    }
