# app/repositories/message_repository.py

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message

class MessageRepository:
    """
    Repository for managing Message entities.
    Provides methods for CRUD operations and specific queries related to messages.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with an async database session.

        :param session: Asynchronous SQLAlchemy session.
        """
        self.session = session

    async def get_all(self) -> List[Message]:
        """
        Retrieve all messages from the database.

        :return: List of all Message objects.
        """
        result = await self.session.execute(select(Message))
        return result.scalars().all()

    async def get_by_id(self, message_id: int) -> Optional[Message]:
        """
        Retrieve a message by its ID.

        :param message_id: The ID of the message to retrieve.
        :return: The Message object if found, otherwise None.
        """
        result = await self.session.execute(select(Message).where(Message.id == message_id))
        return result.scalar_one_or_none()

    async def get_by_chat_id(self, chat_id: int) -> List[Message]:
        """
        Retrieve all messages associated with a specific chat, ordered by creation time.

        :param chat_id: The ID of the chat.
        :return: List of Message objects in the chat, sorted by created_at ascending.
        """
        result = await self.session.execute(
            select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
        )
        return result.scalars().all()

    async def add(self, message: Message) -> Message:
        """
        Add a new message to the database.

        :param message: The Message object to add.
        :return: The added Message object (with generated ID if applicable).
        """
        self.session.add(message)
        await self.session.flush()  # Flush to get the ID without committing
        return message

    async def update(self, message: Message) -> Message:
        """
        Update an existing message in the database.
        Assumes the message object has been modified and is ready to persist.

        :param message: The updated Message object.
        :return: The updated Message object.
        """
        merged_message = await self.session.merge(message)
        await self.session.flush()
        return merged_message

    async def delete(self, message_id: int) -> None:
        """
        Delete a message by its ID.

        :param message_id: The ID of the message to delete.
        """
        message = await self.get_by_id(message_id)
        if message:
            await self.session.delete(message)
            await self.session.flush()