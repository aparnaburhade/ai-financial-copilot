# Proactive AI Financial Copilot

AI-powered backend that analyzes financial data, detects risks and trends, and generates actionable insights using natural language.

---

## Demo

Example question:
> Am I spending too much?

Response:
- Expense ratio: 78%
- Spending increased 12% compared to last month
- High spending detected in Dining and Shopping
- Risk level: Medium
- Recommendation: Reduce discretionary spending by 10–15% to improve savings

---

## What Problem Does It Solve?

Most financial tools show numbers but don’t explain what they mean.

This system allows users to ask:

* *“Am I spending too much?”*
* *“Do I have financial risk?”*
* *“How can I improve my savings?”*

and receive **clear, data-driven recommendations**.

---

## Key Idea

**LLM for reasoning. Python for calculations.**

* LLM → Understands intent & explains results
* Pandas → Performs all financial calculations
* Prevents hallucinations and ensures accuracy

---

## Features

### Financial Health Analysis

* Income vs Expense summary
* Expense ratio calculation
* Month-over-month trends
* Top spending categories

### Risk Detection

* Cashflow risk (expenses > income)
* High spending ratio alerts
* EMI burden analysis
* Overall risk level: **Low / Medium / High**

### Proactive Monitoring

Run a full financial health scan without asking a question.

### Actionable Insights

* Savings recommendations
* Expense control suggestions
* Debt reduction guidance

---

## Tech Stack

* Python
* FastAPI
* Pandas
* LangChain
* OpenAI (GPT-4o-mini)

---

## Architecture

User Question + CSV
→ FastAPI
→ LLM (intent understanding via LangChain)
→ Tool Selection
→ Pandas Analysis
→ Structured Result
→ LLM Explanation
→ Response

---

## Project Structure

```
ai-financial-copilot/
│
├── app.py
├── agent.py
├── tools.py
├── data/
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Create virtual environment

```
python -m venv .venv
.venv\Scripts\activate   # Windows
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Set API key

```
setx OPENAI_API_KEY "YOUR_API_KEY"
```

Restart terminal after setting the key.

---

## Run the Application

```
uvicorn app:app --reload
```

Swagger UI:

```
http://127.0.0.1:8000/docs
```

---

## API Endpoints

**POST /analyze**

```
{
  "question": "Am I spending too much?",
  "csv_path": "data/sample.csv"
}
```

**POST /proactive-check**

```
{
  "csv_path": "data/sample.csv"
}
```

---

## Current Limitations

* Stateless (no persistence)
* Monthly aggregated data only
* Rule-based anomaly detection

---

## Future Improvements

* PostgreSQL integration
* Multi-user support
* Transaction-level analysis
* Real-time monitoring

---

## Why This Project Matters

This project demonstrates:

* Agent-based architecture
* Reliable AI (LLM + deterministic tools)
* Backend system design with FastAPI
* Real-world financial risk analysis


