# app/repositories/chat_repository.py

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chat

class ChatRepository:
    """
    Repository for managing Chat entities.
    Provides methods for CRUD operations and specific queries related to chats.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with an async database session.

        :param session: Asynchronous SQLAlchemy session.
        """
        self.session = session

    async def get_all(self) -> List[Chat]:
        """
        Retrieve all chats from the database.

        :return: List of all Chat objects.
        """
        result = await self.session.execute(select(Chat))
        return result.scalars().all()

    async def get_by_id(self, chat_id: int) -> Optional[Chat]:
        """
        Retrieve a chat by its ID.

        :param chat_id: The ID of the chat to retrieve.
        :return: The Chat object if found, otherwise None.
        """
        result = await self.session.execute(select(Chat).where(Chat.id == chat_id))
        return result.scalar_one_or_none()

    async def get_by_customer_id(self, customer_id: int) -> List[Chat]:
        """
        Retrieve all chats associated with a specific customer.

        :param customer_id: The ID of the customer.
        :return: List of Chat objects for the customer.
        """
        result = await self.session.execute(select(Chat).where(Chat.customer_id == customer_id))
        return result.scalars().all()

    async def add(self, chat: Chat) -> Chat:
        """
        Add a new chat to the database.

        :param chat: The Chat object to add.
        :return: The added Chat object (with generated ID if applicable).
        """
        self.session.add(chat)
        await self.session.flush()  # Flush to get the ID without committing
        return chat

    async def update(self, chat: Chat) -> Chat:
        """
        Update an existing chat in the database.
        Assumes the chat object has been modified and is ready to persist.

        :param chat: The updated Chat object.
        :return: The updated Chat object.
        """
        merged_chat = await self.session.merge(chat)
        await self.session.flush()
        return merged_chat

    async def delete(self, chat_id: int) -> None:
        """
        Delete a chat by its ID.

        :param chat_id: The ID of the chat to delete.
        """
        chat = await self.get_by_id(chat_id)
        if chat:
            await self.session.delete(chat)
            await self.session.flush()