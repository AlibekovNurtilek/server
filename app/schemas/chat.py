# app/schemas/chat.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.db.models import ChatStatus

class ChatBase(BaseModel):
    title: Optional[str] = None
    agent_id: Optional[int] = None
    status: ChatStatus = ChatStatus.open

class ChatCreate(ChatBase):
    pass

class ChatUpdate(ChatBase):
    pass

class Chat(ChatBase):
    id: int
    customer_id: int  # Included in output for clarity, but not in create/update
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}  # For ORM model conversion