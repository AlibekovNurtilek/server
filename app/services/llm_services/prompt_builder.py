"""Prompt builder for LLM messages."""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.customer_services.message_service import MessageService
from app.db.models import Customer, MessageRole

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds prompt messages for LLM requests."""

    def __init__(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt

    @staticmethod
    def _render_user_profile(user: Customer) -> str:
        """Render compact profile for Customer model."""
        try:
            return (
                f"Профиль:\n"
                f"- username: {user.first_name}\n"
                f"- ID: {user.id}\n"
            )
        except Exception as e:
            logger.error("Failed to render user profile: %s", e)
            return "Профиль: белгилүү эмес"

    async def build(
        self,
        *,
        user_message: str,
        user: Optional[Customer] = None,
        chat_id: Optional[int] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """Build messages list for LLM request with conversation history."""
        messages: List[Dict[str, Any]] = []
        
        # System message
        messages.append({"role": "system", "content": self.system_prompt})

        # Optional profile as a separate user turn
        if user is not None:
            profile = self._render_user_profile(user)
            messages.append({"role": "user", "content": profile})

        # Add conversation history if chat_id and db_session are provided
        if chat_id is not None and db_session is not None:
            try:
                message_service = MessageService(db_session)
                history_messages = await message_service.get_messages_by_chat_id(chat_id)
                
                history_messages = sorted(history_messages, key=lambda x: x.created_at)[-4:]
                # Convert history messages to the format expected by LLM
                for msg in history_messages:
                    role = "user" if msg.role == MessageRole.user else "assistant"
                    messages.append({
                        "role": role,
                        "content": msg.content
                    })
                    
                logger.info(f"Added {len(history_messages)} messages from chat history for chat_id: {chat_id}")
                
            except Exception as e:
                logger.error(f"Failed to load conversation history for chat_id {chat_id}: {e}")
                # Continue without history if there's an error

        # Current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages