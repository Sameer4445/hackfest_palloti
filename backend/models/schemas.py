from pydantic import BaseModel, Field
from typing import Optional

class UserApplication(BaseModel):
    age: int = Field(..., ge=18, le=100)
    occupation: str
    location_type: str
    avg_daily_income: float
    work_days_per_month: int = Field(..., ge=1, le=31)
    income_variance: float = Field(..., ge=0, le=1)
    income_source_type: str
    daily_expense: float
    has_bank_account: int = Field(..., ge=0, le=1)
    digital_transaction_usage: float = Field(..., ge=0, le=1)
    avg_work_hours_per_day: float
    location_consistency: float = Field(..., ge=0, le=1)

class ScoringResponse(BaseModel):
    loan_approval: int
    confidence_score: float
    credit_score: int
    decision: str
    risk_level: str
    recommended_loan_options: list[str]
    explanation: str

class CreditRecord(BaseModel):
    application: UserApplication
    result: ScoringResponse
    
