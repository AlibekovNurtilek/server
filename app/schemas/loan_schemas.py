from datetime import date, datetime
from pydantic import BaseModel
from app.db.models import LoanType, LoanStatus
from typing import Dict


class LoanRead(BaseModel):
    id: int
    customer_id: int
    loan_type: LoanType
    principal_amount: float
    interest_rate: float
    start_date: date
    end_date: date
    status: LoanStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



class RequiredDocuments(BaseModel):
    documents: Dict[str, str] 