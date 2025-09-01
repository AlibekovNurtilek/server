from datetime import date, datetime
from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel
from .account_schemas import AccountRead
from .card_schemas import CardRead
from .transaction_schemas import TransactionRead
from .loan_schemas import LoanRead

T = TypeVar("T")

class PaginatedItems(BaseModel, Generic[T]):
    items: List[T]
    page: int
    page_size: int
    total: int

class CustomerRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    middle_name: Optional[str]
    birth_date: date
    passport_number: str
    phone_number: str
    email: str
    address: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedCustomers(BaseModel):
    items: List[CustomerRead]
    page: int
    page_size: int
    total: int