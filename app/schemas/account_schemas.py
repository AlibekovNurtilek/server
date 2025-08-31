# app/schemas/account_schemas.py

from datetime import datetime
from pydantic import BaseModel
from app.db.models import AccountType, AccountStatus

class AccountRead(BaseModel):
    id: int
    account_number: str
    account_type: AccountType
    currency: str
    balance: float
    status: AccountStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True