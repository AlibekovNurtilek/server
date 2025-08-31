# app/services/chat_service.py

import uuid
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.db.repositories.chat_repository import ChatRepository
from app.db.models import Chat, Customer
from app.schemas.chat_schemas import ChatCreate, ChatUpdate, Chat as ChatSchema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatService:
    """
    Service layer for managing chats.
    Handles business logic for chat operations, using schemas for input/output
    to decouple from DB models.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ChatRepository(session)

    async def create_chat(self, chat_data: ChatCreate, customer: Optional[Customer] = None) -> ChatSchema:
        try:
            chat = Chat(
                title=chat_data.title,
                customer_id=customer.id if customer else None,  # Проверка на None
                agent_id=chat_data.agent_id,
                status=chat_data.status
            )
            created_chat = await self.repo.add(chat)
            await self.session.commit()
            await self.session.refresh(created_chat)
            return ChatSchema.model_validate(created_chat)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create chat: {str(e)}")

    async def get_chat_by_id(self, chat_id: int) -> ChatSchema:
        """
        Retrieve a chat by its ID.

        :param chat_id: The ID of the chat.
        :return: The chat as a schema.
        :raises HTTPException: If chat not found.
        """
        chat = await self.repo.get_by_id(chat_id)
        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
        return ChatSchema.model_validate(chat)

    async def get_chats_by_customer(self, customer: Customer) -> List[ChatSchema]:
        """
        Retrieve all chats for a specific customer.

        :param customer: The authenticated Customer object.
        :return: List of chats as schemas.
        """
        chats = await self.repo.get_by_customer_id(customer.id)
        return [ChatSchema.model_validate(c) for c in chats]

    async def update_chat(self, chat_id: int, update_data: ChatUpdate) -> ChatSchema:
        """
        Update an existing chat.

        :param chat_id: The ID of the chat to update.
        :param update_data: Data to update the chat with.
        :return: The updated chat as a schema.
        :raises HTTPException: If chat not found.
        """
        chat = await self.repo.get_by_id(chat_id)
        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

        if update_data.title is not None:
            chat.title = update_data.title
        if update_data.agent_id is not None:
            chat.agent_id = update_data.agent_id
        if update_data.status is not None:
            chat.status = update_data.status

        updated_chat = await self.repo.update(chat)
        await self.session.commit()
        await self.session.refresh(updated_chat)
        return ChatSchema.model_validate(updated_chat)

    async def delete_chat(self, chat_id: int) -> None:
        """
        Delete a chat by its ID.

        :param chat_id: The ID of the chat to delete.
        :raises HTTPException: If chat not found.
        """
        chat = await self.repo.get_by_id(chat_id)
        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
        await self.repo.delete(chat_id)
        await self.session.commit()
