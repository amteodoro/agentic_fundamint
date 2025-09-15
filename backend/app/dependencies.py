import asyncio
import os
from functools import lru_cache
from pydantic import BaseModel
from typing import List, Dict, Any

from langchain_core.tools import BaseTool
from app.financial_agent.llm import ChatOpenRouter
from langchain_mcp_adapters.client import MultiServerMCPClient
from app.financial_agent.mcp_config.config import load_mcp_config
from langchain_core.utils.function_calling import convert_to_openai_tool


class AgentDependencies(BaseModel):
    """A container for the dependencies required by the agent."""
    llm: ChatOpenRouter
    tools_for_llm: List[Dict[str, Any]]
    tools_map: Dict[str, BaseTool]

@lru_cache(maxsize=1)
def get_agent_dependencies() -> AgentDependencies:
    """
    Initializes and returns the dependencies required for the financial agent.

    This function is cached to ensure that the expensive initialization of the LLM,
    tools, and MCP client only happens once.

    Returns:
        An AgentDependencies object containing the initialized LLM and tools.
    """
    # Initialize the language model
    llm = ChatOpenRouter(
        model_name=os.environ.get("OPENROUTER_MODEL", "google/gemini-flash-1.5:free"),
    )

    # Load MCP server configurations and set up the client
    server_configs = load_mcp_config()
    client_config = server_configs["mcpServers"]
    for server_name, config in client_config.items():
        if "transport" not in config:
            config["transport"] = "stdio"

    tool_executor = MultiServerMCPClient(client_config)

    # Asynchronously get the tools and then run the async function
    async def get_tools_async():
        return await tool_executor.get_tools()

    # Run the async function to get tools
    tools = asyncio.run(get_tools_async())

    # Prepare tools for the LLM and create a map for execution
    tools_for_llm = [convert_to_openai_tool(tool) for tool in tools]
    tools_map = {tool.name: tool for tool in tools}

    return AgentDependencies(
        llm=llm,
        tools_for_llm=tools_for_llm,
        tools_map=tools_map,
    )
