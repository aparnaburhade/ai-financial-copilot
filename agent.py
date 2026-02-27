from __future__ import annotations

from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

from tools import trend_analysis, risk_estimation, financial_insights
import os
from pathlib import Path
from dotenv import load_dotenv

# Force load .env from project root
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

print("ENV PATH:", env_path)
print("API KEY LOADED:", os.getenv("OPENAI_API_KEY") is not None)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
@tool
def tool_trend_analysis(csv_path: str) -> Dict[str, Any]:
    """Analyze monthly spending/income trends and top categories from a CSV (monthly aggregated)."""
    return trend_analysis(csv_path)

@tool
def tool_risk_estimation(csv_path: str) -> Dict[str, Any]:
    """Detect monthly/category spending anomalies and estimate cashflow/EMI risk from a CSV (monthly aggregated)."""
    return risk_estimation(csv_path)

@tool
def tool_financial_insights(csv_path: str) -> Dict[str, Any]:
    """Generate savings/interest reduction recommendations using monthly income, EMI/loans, and category patterns."""
    if SAVINGS_COL in df.columns:
        recs.append(f"Current savings amount this month: {round(savings,2)}.")
    return financial_insights(csv_path)

TOOLS = [tool_trend_analysis, tool_risk_estimation, tool_financial_insights]

SYSTEM_PROMPT = """You are a proactive AI financial copilot.
The dataset is monthly aggregated finance history (not individual purchases).
When you say "anomaly", refer to monthly/category spikes vs baseline, not single-transaction anomalies.
When discussing interest savings, treat it as "potential interest savings / debt burden reduction opportunities" (proxy estimate).
If EMI is zero, say "no EMI in the latest month" instead of assuming no debt obligations.
Never claim "no debt obligations" or "debt-free". If EMI is 0, say only: "No EMI payment recorded in the latest month."
If no anomalies are detected, explicitly mention that spending is stable compared to historical patterns.
You MUST choose exactly ONE tool based on the user question:
- tool_trend_analysis: trends / overspending / summary / categories
- tool_risk_estimation: risks / anomalies / spikes / affordability
- tool_financial_insights: saving money / reducing interest / debt / recommendations
After the tool returns, produce:
1) a short insight paragraph (2-4 sentences)
2) 3-6 bullet highlights (each starting with '-')
Do not invent numbers not present in the tool output.
"""

llm = ChatOpenAI(model=MODEL, temperature=0)
llm_with_tools = llm.bind_tools(TOOLS)

def run_agent(question: str, csv_path: str) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {question}\nCSV path: {csv_path}"},
    ]

    first = llm_with_tools.invoke(messages)

    tool_used = "none"
    tool_result = None
    text = ""

    if getattr(first, "tool_calls", None):
        tool_call = first.tool_calls[0]
        tool_used = tool_call["name"]
        args = tool_call.get("args", {}) or {}
        if "csv_path" not in args:
            args["csv_path"] = csv_path

        name_to_tool = {t.name: t for t in TOOLS}
        tool_result = name_to_tool[tool_used].invoke(args)

        messages.append(first)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "name": tool_used,
                "content": str(tool_result),
            }
        )
        final = llm.invoke(messages)
        text = (final.content or "").strip()
    else:
        # fallback (rare)
        text = (first.content or "").strip()

    # Parse bullets
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    highlights = [l[1:].strip() for l in lines if l.startswith("-")]
    insight_lines = [l for l in lines if not l.startswith("-")]
    insight = " ".join(insight_lines).strip()[:1400]

    return {
        "tool_used": tool_used,
        "insight": insight if insight else "Generated insights based on monthly financial analysis.",
        "highlights": highlights[:6],
    }