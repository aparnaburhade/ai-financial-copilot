Proactive AI Financial Copilot 

Proactive AI Financial Copilot is an agent-based backend system that analyzes a user's financial data to detect spending trends, assess financial risk, identify anomalies, and generate actionable recommendations through natural language.

The system combines:

Deterministic financial analysis using Pandas

LLM-based intent understanding and explanation

FastAPI backend for API access

Tool-based agent architecture using LangChain

Key principle: The LLM does NOT perform calculations. All financial metrics are computed using Python tools to ensure accuracy and reduce hallucinations.

Problem Statement

Most financial dashboards show numbers but do not explain what they mean.

This system allows users to ask questions like:

“Am I spending too much?”

“Do I have any financial risk?”

“How can I improve my savings?”

And receive clear, actionable insights based on their financial data.

Features
1. Trend Analysis

Latest month spending summary

Income vs expenditure

Expense ratio (%)

Month-over-month spending change

Top spending categories

2. Risk Estimation

Cashflow risk (expenses > income)

High expense ratio detection

EMI burden analysis

Spending anomaly detection

Overall risk level: Low / Medium / High

3. Financial Insights

Savings improvement suggestions

Expense control recommendations

Debt reduction guidance

Estimated interest savings (proxy)

4. Proactive Monitoring

Runs a full financial health scan without a question

Highlights key risk signals and trends

Tech Stack

Python

FastAPI

Pandas

LangChain

OpenAI (GPT-4o-mini)

Architecture Overview

User Question + CSV
→ FastAPI
→ LLM (intent understanding via LangChain)
→ Appropriate Tool Selected
→ Pandas performs calculations
→ Structured output returned
→ LLM generates explanation
→ Response returned to user

This design ensures:

Accurate calculations

Reduced hallucination

Clear and reliable insights

Project Structure

ai-financial-copilot/
│
├── app.py # FastAPI endpoints
├── agent.py # LLM routing and response generation
├── tools.py # Pandas-based financial analysis logic
├── data/
│ └── monthly_spending_dataset_2020_2025.csv
├── requirements.txt
└── README.md

Setup Instructions
1. Create virtual environment

Windows:
python -m venv .venv
.venv\Scripts\activate

Mac/Linux:
python -m venv .venv
source .venv/bin/activate

2. Install dependencies

pip install -r requirements.txt

3. Set OpenAI API Key

Windows (PowerShell):
setx OPENAI_API_KEY "YOUR_API_KEY"

Restart the terminal after running this.

Mac/Linux:
export OPENAI_API_KEY="YOUR_API_KEY"

Running the Application

uvicorn app:app --reload

Open Swagger UI:

http://127.0.0.1:8000/docs

API Endpoints
POST /analyze

Analyzes a user question and routes it to the appropriate financial tool.

Request body:

{
"question": "Am I spending too much?",
"csv_path": "data/monthly_spending_dataset_2020_2025.csv"
}

POST /proactive-check

Runs a proactive financial health scan.

Request body:

{
"csv_path": "data/monthly_spending_dataset_2020_2025.csv"
}

Dataset Format

The system uses monthly aggregated financial data.

Minimum required columns:

Month / Date

Income

Total Expenditure

Optional:

EMI / Loans

Savings

Category columns (Rent, Groceries, etc.)

The loader automatically normalizes common column name variations.

Why CSV?

This project is a prototype focused on:

Agent architecture

Financial analysis logic

Reliable AI-assisted insights

In production, this would be replaced with:

PostgreSQL database

User authentication

Transaction-level ingestion

Current Limitations

Stateless (no data persistence)

Uses monthly aggregated data (no transaction-level insights)

Rule-based anomaly detection (no predictive ML)

Interest savings is an estimate (no APR/principal details)

Future Improvements

Database integration (PostgreSQL)

Multi-user support

Transaction-level analysis

Real-time monitoring

Caching for performance

Multi-step agent workflows

Why This Project is Agentic

The LLM acts as a decision layer:

Understands user intent

Selects the appropriate analysis tool

Generates a grounded explanation

Instead of fixed rules, the system dynamically decides the next action based on natural language input.