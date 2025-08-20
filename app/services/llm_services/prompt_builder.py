"""Prompt builder for LLM messages."""

import logging
from typing import Any, Dict, List, Optional

from app.db.models import Customer

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

    def build(
        self,
        *,
        user_message: str,
        user: Optional[Customer] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,  # intentionally unused
    ) -> List[Dict[str, Any]]:
        """Build messages list for LLM request."""
        messages: List[Dict[str, Any]] = []
        
        # System message
        messages.append({"role": "system", "content": self.system_prompt})

        # Optional profile as a separate user turn
        if user is not None:
            profile = self._render_user_profile(user)
            messages.append({"role": "user", "content": profile})

        # Current user message
        messages.append({"role": "user", "content": user_message})
        return messages