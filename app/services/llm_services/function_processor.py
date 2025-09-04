"""Function call processor for LLM responses."""

import json
import logging
from typing import List, Optional, Tuple

from app.db.models import Customer
from app.services.mcp_services.tool_arguments import filter_tool_args

from .constants import RESTRICTED_FUNCTIONS, ERROR_MESSAGES
from .mcp_client import call_mcp_tool
from .utils import parse_func_call

logger = logging.getLogger(__name__)


class FunctionProcessor:
    """Processes function calls from LLM responses."""

    @staticmethod
    def check_authorization_required(func_calls: List[str], user: Optional[Customer]) -> Optional[str]:
        """Check if any function requires authorization and user is not logged in."""
        if user is None and func_calls:
            for fc in func_calls:
                try:
                    name, _ = parse_func_call(fc)
                    if name in RESTRICTED_FUNCTIONS:
                        return name
                except Exception as e:
                    logger.error("Error parsing func call %s: %s", fc, e)
                    continue
        return None

    @staticmethod
    def get_error_message(lang: str) -> str:
        """Get localized error message for authorization requirement."""
        return ERROR_MESSAGES.get(lang, ERROR_MESSAGES["ru"])

    @staticmethod
    def format_sse_response(content: str) -> str:
        """Format content as SSE response."""
        sse_data = {
            "choices": [{
                "delta": {
                    "content": content
                }
            }]
        }
        return f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"

    @staticmethod
    async def process_function_calls(
        func_calls: List[str], 
        user: Optional[Customer], 
        lang: str
    ) -> Tuple[List[str], bool]:
        """
        Process function calls and return results.
        
        Args:
            func_calls: List of function call strings to process
            user: Optional Customer object containing user information
            lang: Language code for the request
        
        Returns:
            Tuple of (results, is_faq_call) where results is a list of tool outputs
            and is_faq_call indicates if any call was to get_faq_by_category
        """
        results: List[str] = []
        is_faq = False
        
        for fc in func_calls:
            try:
                name, kwargs = parse_func_call(fc)
                logger.info("Parsed function call: %s with args: %s", name, kwargs)
                
                if name == "get_faq_by_category":
                    is_faq = True
                
                # Add user ID if user is provided and not in kwargs
                if user and "customer_id" not in kwargs:
                    kwargs["customer_id"] = user.id
                
                # Add language if not in kwargs
                if "lang" not in kwargs:
                    kwargs["lang"] = lang
                
                # Filter tool arguments
                kwargs = filter_tool_args(name, kwargs)
                logger.info("Calling MCP tool: %s with args: %s", name, kwargs)
                
                # Call the tool
                output = await call_mcp_tool(name, kwargs)
                results.append(output or "")
                
            except Exception as e:
                logger.error(
                    "Error processing function call %s with args %s: %s",
                    name,
                    kwargs,
                    str(e),
                    exc_info=True  # Включаем полный стек ошибки для детального логирования
                )
                results.append(f"Ошибка: {str(e)}")  # LLM will handle politely
        
        return results, is_faq