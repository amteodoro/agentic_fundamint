import asyncio
import os
from functools import lru_cache
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from langchain_core.tools import BaseTool
from app.financial_agent.llm import ChatOpenRouter
from langchain_mcp_adapters.client import MultiServerMCPClient
from app.financial_agent.mcp_config.config import load_mcp_config
from langchain_core.utils.function_calling import convert_to_openai_tool
from app.financial_agent.tools.registry import create_financial_tools_registry

logger = logging.getLogger(__name__)


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
    logger.info("Initializing agent dependencies...")
    
    # Initialize the language model
    llm = ChatOpenRouter(
        model_name=os.environ.get("OPENROUTER_MODEL", "google/gemini-flash-1.5:free"),
    )
    logger.info(f"Initialized LLM: {llm.model_name}")

    # Load MCP server configurations and set up the client
    server_configs = load_mcp_config()
    client_config = server_configs["mcpServers"]
    for server_name, config in client_config.items():
        if "transport" not in config:
            config["transport"] = "stdio"

    tool_executor = MultiServerMCPClient(client_config)

    # Asynchronously get external tools (like Tavily)
    async def get_external_tools_async():
        return await tool_executor.get_tools()

    # Run the async function to get external tools
    external_tools = asyncio.run(get_external_tools_async())
    logger.info(f"Loaded {len(external_tools)} external tools")
    
    # Find Tavily tool for financial tools integration
    tavily_tool = None
    for tool in external_tools:
        if 'tavily' in tool.name.lower() or 'search' in tool.name.lower():
            tavily_tool = tool
            logger.info(f"Found Tavily tool: {tool.name}")
            break
    
    # Initialize financial analysis tools with Tavily integration
    financial_tools_registry = create_financial_tools_registry(tavily_tool=tavily_tool, llm=llm)
    financial_tools = financial_tools_registry.get_all_tools()
    logger.info(f"Initialized {len(financial_tools)} financial analysis tools")
    
    # Combine external and internal tools
    all_tools = external_tools + financial_tools
    logger.info(f"Total tools available: {len(all_tools)}")
    
    # Log all available tools
    for tool in all_tools:
        logger.info(f"  - {tool.name}: {tool.description[:100]}...")

    # Prepare tools for the LLM and create a map for execution
    tools_for_llm = [convert_to_openai_tool(tool) for tool in all_tools]
    tools_map = {tool.name: tool for tool in all_tools}

    logger.info("Agent dependencies initialization completed")
    
    return AgentDependencies(
        llm=llm,
        tools_for_llm=tools_for_llm,
        tools_map=tools_map,
    )
