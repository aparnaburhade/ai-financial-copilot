from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    question: str = Field(..., description="The user's question about the financial data.")
    csv_path: str = Field(default="data/monthly_spending_dataset_2020_2025.csv", description="Path to the CSV file containing the financial data.")

class AnalyzeResponse(BaseModel):
    tool_used: str
    insight: str
    highlights: list[str]

class ProactiveRequest(BaseModel):
    csv_path: str = Field(default="data/monthly_spending_dataset_2020_2025.csv", description="Path to the CSV file containing the financial data.")

class ProactiveResponse(BaseModel):
    insight: str
    highlights: list[str]


    