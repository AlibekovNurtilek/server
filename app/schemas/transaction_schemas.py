from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.db.models import TransactionType, TransactionStatus

class TransactionRead(BaseModel):
    id: int
    from_account_id: Optional[int]
    to_account_id: Optional[int]
    transaction_type: TransactionType
    amount: float
    currency: str
    description: Optional[str]
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True