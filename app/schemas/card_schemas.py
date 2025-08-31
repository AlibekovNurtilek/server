from datetime import date, datetime
from pydantic import BaseModel
from app.db.models import CardType, CardStatus

class CardRead(BaseModel):
    id: int
    account_id: int
    card_number: str
    card_type: CardType
    expiration_date: date
    status: CardStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True