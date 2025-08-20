# app/schemas/message.py

from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from app.db.models import MessageRole

class MessageBase(BaseModel):
    chat_id: int
    role: MessageRole
    content: str

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    content: Optional[str] = None

class Message(MessageBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}  # Для преобразования из ORM модели