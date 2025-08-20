"""LLM client for AI Bank assistant."""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
from app.db.models import Customer
from app.services.llm_services.system_promt import get_system_prompt, get_faq_system_prompt, get_tool_response_system_prompt

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
    """

    def __init__(
        self,
        *,
        llm_url: str = "https://chat.aitil.kg/suroo",
        model: str = "aitil",
        temperature: float = 0.5,
        default_language: str = "ky",
        request_timeout: Optional[float] = None,
    ) -> None:
        self.llm_url = llm_url
        self.model = model
        self.temperature = temperature
        self.default_language = default_language
        self.request_timeout = request_timeout
        self.function_processor = FunctionProcessor()

    async def astream_answer(
        self,
        message: str,
        *,
        language: Optional[str] = None,
        user: Optional[Customer] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream answer with function call processing."""
        lang = language or self.default_language
        payload = self._build_payload(
            message=message,
            language=lang,
            user=user,
            stream=True,
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
            yield self.function_processor.format_sse_response(error_message)
            yield "data: [DONE]\n\n"
            return

        # If no function calls, stream the original response
        if not func_calls:
            for part in parts:
                yield self.function_processor.format_sse_response(part)
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
        new_messages = builder.build(user_message=final_user_message, user=user)
        
        new_payload = {
            "model": self.model,
            "messages": new_messages,
            "temperature": self.temperature,
            "stream": True,
        }
        logger.info("Final LLM request payload: %s", json.dumps(new_payload, ensure_ascii=False, indent=2))
        
        # Stream the final response
        async for chunk in self._sse_stream(new_payload):
            yield chunk

    def _build_payload(
        self,
        *,
        message: str,
        language: str,
        user: Optional[Customer],
        stream: bool,
    ) -> Dict[str, Any]:
        """Build request payload for LLM."""
        system_prompt = get_system_prompt(language)
        builder = PromptBuilder(system_prompt)
        messages = builder.build(user_message=message, user=user)

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


def build_llm_client() -> AitilLLMClient:
    """Build and return LLM client instance."""
    return AitilLLMClient(
        llm_url="https://chat.aitil.kg/suroo",
        model="aitil",
        temperature=0.5,
        default_language="ky",
        request_timeout=None,
    )