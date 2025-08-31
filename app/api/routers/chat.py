# app/routers/chat.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer, get_db_session, get_optional_customer
from app.services.customer_services.chat_service import ChatService
from app.schemas.chat import ChatCreate, ChatUpdate, Chat
from app.db.models import Customer
from app.api.deps import get_db_session

router = APIRouter(prefix="/chats", tags=["chats"])

@router.get("/", response_model=List[Chat])
async def get_all_chats(
    current_user: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retrieve all chats for the authenticated customer.
    """
    service = ChatService(session)
    try:
        return await service.get_chats_by_customer(current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{chat_id}", response_model=Chat)
async def get_chat(
    chat_id: int,
    current_user: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retrieve a chat by its ID, ensuring it belongs to the authenticated customer.
    """
    service = ChatService(session)
    try:
        chat = await service.get_chat_by_id(chat_id)
        if chat.customer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this chat")
        return chat
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/customer/me", response_model=List[Chat])
async def get_chats_by_customer(
    current_user: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retrieve all chats for the authenticated customer.
    """
    service = ChatService(session)
    try:
        return await service.get_chats_by_customer(current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/", response_model=Chat, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    current_user: Customer = Depends(get_optional_customer),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create a new chat for the authenticated customer.
    """
    service = ChatService(session)
    try:
        return await service.create_chat(chat_data, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{chat_id}", response_model=Chat)
async def update_chat(
    chat_id: int,
    update_data: ChatUpdate,
    current_user: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Update an existing chat, ensuring it belongs to the authenticated customer.
    """
    service = ChatService(session)
    try:
        chat = await service.get_chat_by_id(chat_id)
        if chat.customer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this chat")
        return await service.update_chat(chat_id, update_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: int,
    current_user: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Delete a chat by its ID, ensuring it belongs to the authenticated customer.
    """
    service = ChatService(session)
    try:
        chat = await service.get_chat_by_id(chat_id)
        if chat.customer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this chat")
        await service.delete_chat(chat_id)
    except HTTPException as e:
        raise e