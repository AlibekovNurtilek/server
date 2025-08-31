from pydantic import BaseModel
from typing import Optional

class ConversationRequest(BaseModel):
    message: str
    language: str = "ky"
    chat_id: Optional[int] = None