"""MCP client for tool calls."""

import asyncio
import logging
from typing import Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


async def call_mcp_tool(tool_name: str, tool_args: Dict[str, Any]) -> Optional[str]:
    """Call MCP tool with given name and arguments."""
    params = StdioServerParameters(
        command="python",
        args=["-m", "app.mcp.mcp_server"],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()

            # Wait for tools to register
            await asyncio.sleep(0.5)

            # Get list of tools to ensure requested tool exists
            tools = await session.list_tools()
            if not any(t.name == tool_name for t in tools.tools):
                raise ValueError(f"Tool {tool_name} not found on MCP server")

            # Call the tool
            result = await session.call_tool(tool_name, tool_args)
            return result.content[0].text if result.content else None