# app/routers/message.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.services.message_service import MessageService
from app.schemas.message import MessageCreate, MessageUpdate, Message

router = APIRouter(prefix="/messages", tags=["messages"])

@router.get("/", response_model=List[Message])
async def get_all_messages(session: AsyncSession = Depends(get_db_session)):
    """
    Retrieve all messages.
    """
    service = MessageService(session)
    messages = await service.get_messages_by_chat_id(chat_id=None)  # Passing None to get all
    return messages

@router.get("/{message_id}", response_model=Message)
async def get_message(message_id: int, session: AsyncSession = Depends(get_db_session)):
    """
    Retrieve a message by its ID.
    """
    service = MessageService(session)
    try:
        return await service.get_message_by_id(message_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/chat/{chat_id}", response_model=List[Message])
async def get_messages_by_chat(chat_id: int, session: AsyncSession = Depends(get_db_session)):
    """
    Retrieve all messages for a specific chat.
    """
    service = MessageService(session)
    return await service.get_messages_by_chat_id(chat_id)

@router.post("/", response_model=Message, status_code=status.HTTP_201_CREATED)
async def create_message(message_data: MessageCreate, session: AsyncSession = Depends(get_db_session)):
    """
    Create a new message.
    """
    service = MessageService(session)
    try:
        return await service.create_message(message_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{message_id}", response_model=Message)
async def update_message(message_id: int, update_data: MessageUpdate, session: AsyncSession = Depends(get_db_session)):
    """
    Update an existing message.
    """
    service = MessageService(session)
    try:
        return await service.update_message(message_id, update_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: int, session: AsyncSession = Depends(get_db_session)):
    """
    Delete a message by its ID.
    """
    service = MessageService(session)
    try:
        await service.delete_message(message_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))