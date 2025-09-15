
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import os
import asyncio
from typing import Dict, Any, Optional
from app.financial_agent.graph import graph
from app.financial_agent.llm import ChatOpenRouter
from langchain_mcp_adapters.client import MultiServerMCPClient
from app.financial_agent.mcp_config.config import load_mcp_config
from langchain_core.utils.function_calling import convert_to_openai_tool
from app.dependencies import get_agent_dependencies, AgentDependencies
from langchain_core.messages import HumanMessage, SystemMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    thread_id: str
    context: Optional[Dict[str, Any]] = None


@router.post("")
async def chat(
    request: ChatRequest,
    agent_deps: AgentDependencies = Depends(get_agent_dependencies),
):
    """
    Handles a chat request by invoking the financial agent graph.

    This endpoint receives a user's message and a thread ID, injects the
    necessary dependencies (LLM, tools, tool maps), and then calls the
    LangGraph agent to get a response.

    Args:
        request: A ChatRequest object containing the user's message and thread ID.
        agent_deps: Dependencies for the agent, including the LLM and tools.

    Returns:
        A dictionary containing the agent's final response message.
    """
    logger.info(f"Received chat request: {request.model_dump_json()}")

    config = {
        "configurable": {
            "thread_id": request.thread_id,
            "llm": agent_deps.llm,
            "tools": agent_deps.tools_for_llm,
            "tools_map": agent_deps.tools_map,
        }
    }

    messages = []
    if request.context and request.context.get('ticker'):
        ticker = request.context['ticker']
        messages.append(SystemMessage(content=f"The user is currently viewing information for the stock with the ticker symbol: {ticker}. All questions should be considered in this context unless specified otherwise."))
    
    messages.append(HumanMessage(content=request.message))

    try:
        logger.info(f"Invoking agent with messages: {messages}")
        response = await graph.ainvoke({"messages": messages}, config)
        logger.info(f"Agent response: {response}")
        
        # Return the last message from the agent's response
        return {"message": response["messages"][-1].content}
    except Exception as e:
        logger.error(f"Error during agent invocation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing your request.")
