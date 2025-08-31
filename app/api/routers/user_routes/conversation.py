# app/api/routes/chat.py
from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_customer
from app.schemas.conversation_schemas import ConversationRequest
from app.services.llm_services.llm_client import build_llm_client
from app.db.models import Customer
from app.api.deps import get_db_session

router = APIRouter(prefix="/api/conversation", tags=["Conversation"])

@router.post("/")
async def conversation(
    payload: ConversationRequest,
    request: Request,
    current_user: Optional[Customer] = Depends(get_optional_customer),
    session: AsyncSession = Depends(get_db_session),
):
    llm_client = build_llm_client(db_session=session)

    return StreamingResponse(
        llm_client.astream_answer(
            message=payload.message,
            user=current_user,
            language=payload.language or "ky",
            chat_id=payload.chat_id if payload.chat_id is not None else None,
        ),
        media_type="text/event-stream",
    )

