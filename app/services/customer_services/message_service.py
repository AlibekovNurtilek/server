# app/services/message_service.py

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.db.repositories.message_repository import MessageRepository
from app.db.models import Message
from app.schemas.message_schemas import MessageCreate, MessageUpdate, MessageSchema as MessageSchema

class MessageService:
    """
    Service layer for managing messages.
    Handles business logic for message operations, using schemas for input/output
    to decouple from DB models.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MessageRepository(session)

    async def create_message(self, message_data: MessageCreate) -> MessageSchema:
        """
        Create a new message.

        :param message_data: Input data for creating a message.
        :return: The created message as a schema.
        """
        message = Message(
            chat_id=message_data.chat_id,
            role=message_data.role,
            content=message_data.content
        )
        created_message = await self.repo.add(message)
        await self.session.commit()
        await self.session.refresh(created_message)
        return MessageSchema.model_validate(created_message)

    async def get_message_by_id(self, message_id: int) -> MessageSchema:
        """
        Retrieve a message by its ID.

        :param message_id: The ID of the message.
        :return: The message as a schema.
        :raises HTTPException: If message not found.
        """
        message = await self.repo.get_by_id(message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        return MessageSchema.model_validate(message)

    async def get_messages_by_chat_id(self, chat_id: int) -> List[MessageSchema]:
        """
        Retrieve all messages for a specific chat.

        :param chat_id: The ID of the chat.
        :return: List of messages as schemas.
        """
        messages = await self.repo.get_by_chat_id(chat_id)
        return [MessageSchema.model_validate(m) for m in messages]

    async def update_message(self, message_id: int, update_data: MessageUpdate) -> MessageSchema:
        """
        Update an existing message.

        :param message_id: The ID of the message to update.
        :param update_data: Data to update the message with.
        :return: The updated message as a schema.
        :raises HTTPException: If message not found.
        """
        message = await self.repo.get_by_id(message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

        if update_data.content is not None:
            message.content = update_data.content

        updated_message = await self.repo.update(message)
        await self.session.commit()
        await self.session.refresh(updated_message)
        return MessageSchema.model_validate(updated_message)

    async def delete_message(self, message_id: int) -> None:
        """
        Delete a message by its ID.

        :param message_id: The ID of the message to delete.
        :raises HTTPException: If message not found.
        """
        message = await self.repo.get_by_id(message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        await self.repo.delete(message_id)
        await self.session.commit()