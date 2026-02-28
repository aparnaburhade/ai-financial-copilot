from fastapi import FastAPI, HTTPException
from schemas import AnalyzeRequest, AnalyzeResponse, ProactiveRequest, ProactiveResponse
from agent import run_agent
from tools import proactive_check

app = FastAPI(title="Proactive AI Financial Copilot", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    try:
        result = run_agent(req.question, req.csv_path)
        return AnalyzeResponse(**result)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV not found: {req.csv_path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/proactive-check", response_model=ProactiveResponse)
def proactive(req: ProactiveRequest):
    try:
        out = proactive_check(req.csv_path)
        return ProactiveResponse(insight=out["summary"], highlights=out["highlights"])
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV not found: {req.csv_path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
