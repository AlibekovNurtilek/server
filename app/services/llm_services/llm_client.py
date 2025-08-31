"""LLM client for AI Bank assistant."""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
from app.db.models import Customer, MessageRole
from app.services.llm_services.system_promt import get_system_prompt, get_faq_system_prompt, get_tool_response_system_prompt
from app.services.customer_services.message_service import MessageService
from app.schemas.message import MessageCreate
from sqlalchemy.ext.asyncio import AsyncSession

from .function_processor import FunctionProcessor
from .prompt_builder import PromptBuilder
from .utils import extract_func_calls

logger = logging.getLogger(__name__)


class AitilLLMClient:
    """
    Async client that:
    - Builds messages with PromptBuilder
    - Streams SSE tokens
    - Processes function calls
    - Saves messages to database
    """

    def __init__(
        self,
        *,
        llm_url: str = "https://chat.aitil.kg/suroo",
        model: str = "aitil",
        temperature: float = 0.5,
        default_language: str = "ky",
        request_timeout: Optional[float] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> None:
        self.llm_url = llm_url
        self.model = model
        self.temperature = temperature
        self.default_language = default_language
        self.request_timeout = request_timeout
        self.function_processor = FunctionProcessor()
        self.db_session = db_session

    async def _save_messages_to_db(
        self, 
        user_message: str, 
        assistant_response: str, 
        chat_id: int
    ) -> None:
        """
        Save user message and assistant response to database.
        
        :param user_message: The user's message content
        :param assistant_response: The assistant's response content
        :param chat_id: The chat ID
        """
        if not self.db_session:
            logger.warning("No database session provided, skipping message save")
            return
            
        try:
            message_service = MessageService(self.db_session)
            
            # Save user message
            user_msg_data = MessageCreate(
                chat_id=chat_id,
                role=MessageRole.user,
                content=user_message
            )
            await message_service.create_message(user_msg_data)
            
            # Save assistant response
            assistant_msg_data = MessageCreate(
                chat_id=chat_id,
                role=MessageRole.assistant,
                content=assistant_response
            )
            await message_service.create_message(assistant_msg_data)
            
            logger.info(f"Messages saved to database for chat_id: {chat_id}")
            
        except Exception as e:
            logger.error(f"Failed to save messages to database: {e}")
            # Don't raise the exception to avoid breaking the main flow

    async def astream_answer(
        self,
        message: str,
        *,
        language: Optional[str] = None,
        user: Optional[Customer] = None,
        chat_id: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream answer with function call processing and message saving."""
        lang = language or self.default_language
        payload = await self._build_payload(
            message=message,
            language=lang,
            user=user,
            stream=True,
            chat_id=chat_id,
        )
        
        # Collect initial response text for function analysis
        parts: List[str] = []
        async for chunk in self._raw_stream(payload):
            parts.append(chunk)
        
        full_text = "".join(parts)
        logger.info("Full initial response text: %s", full_text)
        func_calls = extract_func_calls(full_text)
        
        # Check if authorization is required
        restricted_func = self.function_processor.check_authorization_required(func_calls, user)
        if restricted_func:
            error_message = self.function_processor.get_error_message(lang)
            
            # Save messages to DB if user is authorized and chat_id exists
            if chat_id:
                try:
                    chat_id_int = int(chat_id)
                    await self._save_messages_to_db(message, error_message, chat_id_int)
                except (ValueError, TypeError):
                    logger.error(f"Invalid chat_id format: {chat_id}")
            
            yield self.function_processor.format_sse_response(error_message)
            yield "data: [DONE]\n\n"
            return

        # If no function calls, stream the original response
        if not func_calls:
            # Collect response chunks for saving
            response_chunks: List[str] = []
            
            for part in parts:
                response_chunks.append(part)
                yield self.function_processor.format_sse_response(part)
            
            # Save messages to DB if user is authorized and chat_id exists
            if chat_id:
                try:
                    chat_id_int = int(chat_id)
                    full_response = "".join(response_chunks)
                    await self._save_messages_to_db(message, full_response, chat_id_int)
                except (ValueError, TypeError):
                    logger.error(f"Invalid chat_id format: {chat_id}")
            
            yield "data: [DONE]\n\n"
            return

        # Process function calls
        results, is_faq = await self.function_processor.process_function_calls(
            func_calls, user, lang
        )
        
        tool_response = "\n".join(results)
        
        # Build system prompt for final response
        if is_faq:
            new_system_prompt = get_faq_system_prompt(lang, user, tool_response)
            final_user_message = message
        else:
            new_system_prompt = get_tool_response_system_prompt(lang, user, tool_response)
            final_user_message = message

        # Build final LLM request
        builder = PromptBuilder(new_system_prompt)
        new_messages = await builder.build(user_message=final_user_message, user=user)
        
        new_payload = {
            "model": self.model,
            "messages": new_messages,
            "temperature": self.temperature,
            "stream": True,
        }
        logger.info("Final LLM request payload: %s", json.dumps(new_payload, ensure_ascii=False, indent=2))
        
        # Stream the final response and collect chunks for saving
        response_chunks: List[str] = []
        
        async for chunk in self._sse_stream(new_payload):
            # Extract content from SSE format for saving
            if chunk.startswith("data: ") and chunk != "data: [DONE]\n\n":
                try:
                    data = chunk[len("data: "):].strip()
                    if data and data != "[DONE]":
                        obj = json.loads(data)
                        content = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            response_chunks.append(content)
                except json.JSONDecodeError:
                    pass
            
            yield chunk
        
        # Save messages to DB if user is authorized and chat_id exists
        if chat_id:
            try:
                chat_id_int = int(chat_id)
                full_response = "".join(response_chunks)
                await self._save_messages_to_db(message, full_response, chat_id_int)
            except (ValueError, TypeError):
                logger.error(f"Invalid chat_id format: {chat_id}")

    async def _build_payload(
        self,
        *,
        message: str,
        language: str,
        user: Optional[Customer],
        stream: bool,
        chat_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Build request payload for LLM."""
        system_prompt = get_system_prompt(language)
        builder = PromptBuilder(system_prompt)
        messages = await builder.build(
            user_message=message, 
            user=user, 
            chat_id=chat_id, 
            db_session=self.db_session
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": stream,
        }
        logger.info("LLM request payload: %s", json.dumps(payload, ensure_ascii=False, indent=2))
        return payload

    async def _raw_stream(self, payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream raw text content for function analysis."""
        headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
        timeout = None if self.request_timeout is None else httpx.Timeout(self.request_timeout)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", self.llm_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                        chunk = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        continue

    async def _sse_stream(self, payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream SSE formatted response to client."""
        headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
        timeout = None if self.request_timeout is None else httpx.Timeout(self.request_timeout)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", self.llm_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        yield "data: [DONE]\n\n"
                        break
                    try:
                        obj = json.loads(data)
                        chunk = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if chunk:
                            yield self.function_processor.format_sse_response(chunk)
                    except json.JSONDecodeError:
                        continue


def build_llm_client(db_session: Optional[AsyncSession] = None) -> AitilLLMClient:
    """Build and return LLM client instance."""
    return AitilLLMClient(
        llm_url="https://chat.aitil.kg/mcp_suroo",
        model="aitil",
        temperature=0.5,
        default_language="ky",
        request_timeout=None,
        db_session=db_session,
    )