from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.db.models import LoanApplicationStatus, CardApplicationStatus, CardType


# ---------- Loan Application Schemas ----------
class LoanApplicationRead(BaseModel):
    id: int
    customer_id: int
    loan_type: str
    amount: float
    term_months: int
    interest_rate: float
    own_contribution: Optional[float] = None
    collateral: Optional[str] = None
    status: LoanApplicationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoanApplicationUpdateStatus(BaseModel):
    status: LoanApplicationStatus


# ---------- Card Application Schemas ----------
class CardApplicationRead(BaseModel):
    id: int
    customer_id: int
    account_id: int
    card_type: CardType
    card_name: str
    status: CardApplicationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CardApplicationUpdateStatus(BaseModel):
    status: CardApplicationStatus
