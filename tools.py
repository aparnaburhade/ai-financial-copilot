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
        raise ValueError(
            f"CSV missing required columns: {missing}. Found columns: {list(df.columns)}"
        )

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


def trend_analysis(csv_path: str) -> Dict[str, Any]:
    df = _load_monthly(csv_path)
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else None

    total_exp = float(last[TOTAL_EXP_COL])
    income = float(last[INCOME_COL])

    mom_change = None
    if prev is not None and not pd.isna(prev[TOTAL_EXP_COL]):
        mom_change = _pct_change(total_exp, float(prev[TOTAL_EXP_COL]))

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
            top_categories[str(k)] = round(float(v), 2)

    expense_ratio_pct = round((total_exp / income) * 100, 1) if income else None

    return {
        "month": str(last[MONTH_COL].date()),
        "total_expenditure": round(total_exp, 2),
        "income": round(income, 2),
        "expense_ratio_pct": expense_ratio_pct,
        "month_over_month_spend_change_pct": mom_change,
        "top_categories_latest_month": top_categories,
    }


def risk_estimation(csv_path: str) -> Dict[str, Any]:
    df = _load_monthly(csv_path)
    last = df.iloc[-1]

    total_exp = float(last[TOTAL_EXP_COL])
    income = float(last[INCOME_COL]) if not pd.isna(last[INCOME_COL]) else 0.0

    expense_ratio = (total_exp / income) if income else 999.0

    #emi = float(last[EMI_COL]) if EMI_COL in df.columns and not pd.isna(last.get(EMI_COL)) else 0.0
    emi = 0.0
    if EMI_COL in df.columns:
        val = last.get(EMI_COL)
        if val is not None and not pd.isna(val):
            emi = float(val)
    emi_ratio = (emi / income) if income else 0.0

    anomalies: List[dict] = []

    # MoM total spend spike
    if len(df) >= 2:
        prev_total = float(df.iloc[-2][TOTAL_EXP_COL])
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

    # "High vs last 12 months" spike (helps surface anomalies even when MoM is calm)
    window = df.tail(13)  # 12 months + current
    if len(window) >= 2:
        prev12 = window.iloc[:-1]
        prev12_max = float(prev12[TOTAL_EXP_COL].max())
        if prev12_max > 0 and total_exp >= 1.15 * prev12_max:
            anomalies.append({
                "type": "spend_high_vs_12m",
                "month": str(last[MONTH_COL].date()),
                "value": round(total_exp, 2),
                "prev12m_max": round(prev12_max, 2),
                "reason": "Total expenditure is unusually high compared to the last 12 months.",
            })

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
            base_avg = float(baseline[cat].mean(skipna=True))
            curr = float(last[cat]) if not pd.isna(last[cat]) else 0.0
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
        "expense_ratio_pct": round(expense_ratio * 100, 1) if income else None,
        "anomalies": anomalies[:8],
        "emi_amount_latest_month": round(emi, 2),
        "emi_ratio_pct_latest_month": round(emi_ratio * 100, 1) if income else None,
        "emi_note": "EMI/loan payment shown is for the latest month only. Do not infer overall debt status from this value.",
    }


def financial_insights(csv_path: str) -> Dict[str, Any]:
    df = _load_monthly(csv_path)
    last = df.iloc[-1]

    income = float(last[INCOME_COL]) if not pd.isna(last[INCOME_COL]) else 0.0
    total_exp = float(last[TOTAL_EXP_COL]) if not pd.isna(last[TOTAL_EXP_COL]) else 0.0

    emi = float(last[EMI_COL]) if EMI_COL in df.columns and not pd.isna(last.get(EMI_COL)) else 0.0
    savings = float(last[SAVINGS_COL]) if SAVINGS_COL in df.columns and not pd.isna(last.get(SAVINGS_COL)) else 0.0

    emi_ratio = (emi / income) if income else 0.0
    savings_ratio = (savings / income) if income else 0.0

    # Conservative proxy for "interest savings"
    est_interest_savings = 0.0
    if emi > 0 and emi_ratio >= 0.25:
        est_interest_savings = round(emi * 0.05, 2)  # 5% of EMI as proxy

    recs: List[str] = []

    if income:
        recs.append(
            f"Expense-to-income ratio is ~{round((total_exp / income) * 100, 1)}%. Targeting <80% improves stability."
        )
    if emi_ratio >= 0.30:
        recs.append(
            "EMI/Loans are a high portion of income. Consider prepaying principal or refinancing to reduce interest burden."
        )
    elif emi > 0:
        recs.append(
            "If you have multiple loans/cards, prioritize highest-interest debt first (avalanche method)."
        )

    if SAVINGS_COL in df.columns and income:
        if savings_ratio < 0.10:
            recs.append(
                "Savings rate looks low. Automate a fixed transfer to savings right after income is received."
            )
        else:
            recs.append(f"Savings rate is ~{round(savings_ratio*100,1)}%. Keep it consistent month-to-month.")

    # Add a discretionary spending note if present
    for candidate in ["Shopping & Wants (₹)", "Shopping", "Shopping_&_Wants", "shopping", "shopping_wants"]:
        if candidate in df.columns:
            val = float(last[candidate]) if not pd.isna(last[candidate]) else 0.0
            recs.append(f"{candidate}: {round(val,2)}. Setting a cap can reduce discretionary spending swings.")
            break

    return {
        "month": str(last[MONTH_COL].date()),
        "estimated_interest_savings": float(est_interest_savings),
        "key_recommendations": recs[:5],
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
    if f["estimated_interest_savings"] > 0:
        highlights.append(f"Potential interest savings estimate: ~{f['estimated_interest_savings']:.0f}/month (proxy)")

    return {
        "summary": "Proactive scan completed: identified trends, risk signals, and savings opportunities.",
        "highlights": highlights[:6],
    }