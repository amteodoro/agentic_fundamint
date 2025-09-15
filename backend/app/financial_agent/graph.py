import os
import json
import logging
import asyncio
from typing import TypedDict, Annotated, Sequence, Any
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, END

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _format_tool_response(response: Any) -> str:
    """Formats the tool response into a JSON string for consistent processing."""
    logging.info(f"Formatting tool response: {response}")
    if isinstance(response, (dict, list)):
        # If it's already a dict or list, dump it to a JSON string.
        formatted_str = json.dumps(response, indent=2)
        logging.info(f"Formatted dict/list response: {formatted_str}")
        return formatted_str
    elif isinstance(response, str):
        try:
            # If it's a string, try to parse it as JSON and re-serialize.
            # This validates and standardizes the JSON format.
            parsed_json = json.loads(response)
            formatted_str = json.dumps(parsed_json, indent=2)
            logging.info(f"Validated and formatted JSON string: {formatted_str}")
            return formatted_str
        except json.JSONDecodeError:
            # If it's a string but not valid JSON (e.g., an error message),
            # wrap it in a JSON structure.
            logging.warning(f"Response is a non-JSON string. Wrapping it: {response}")
            formatted_str = json.dumps({"message": response}, indent=2)
            return formatted_str
    else:
        # For any other data type, convert to string and wrap in a JSON structure.
        logging.warning(f"Response is of an unexpected type. Converting to string and wrapping: {type(response)}")
        formatted_str = json.dumps({"value": str(response)}, indent=2)
        return formatted_str

# Define the state for our agent - it should only contain serializable data
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]

# The agent's thinking node, now accepting a config
async def run_agent(state, config):
    logging.info("---AGENT THINKING---")
    logging.info(f"---CONFIG: {config}---")
    llm = config["configurable"]["llm"]
    tools = config["configurable"]["tools"]
    messages = state["messages"]

    logging.info(f"---MESSAGES TO LLM (Count: {len(messages)})---")
    for i, msg in enumerate(messages):
        logging.info(f"  Message {i}: Type={type(msg).__name__}, Content='{msg.content}', Tool Calls={hasattr(msg, 'tool_calls') and msg.tool_calls}")

    logging.info(f"Invoking LLM: {llm.__class__.__name__}")
    try:
        response = await llm.ainvoke(messages, tools=tools)
        logging.info(f"---AGENT RAW RESPONSE: {response}---")
    except Exception as e:
        logging.error(f"---ERROR DURING LLM INVOCATION: {e}---", exc_info=True)
        error_message = f"An error occurred while communicating with the LLM: {e}"
        return {"messages": [AIMessage(content=error_message)]}
    
    return {"messages": [response]}

# The tool execution node, now accepting a config
async def execute_tools(state, config):
    logging.info("---EXECUTING TOOLS---")
    tools_map = config["configurable"]["tools_map"]
    last_message = state["messages"][-1]
    
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        logging.warning("No tool calls found in the last message.")
        return {"messages": []}
        
    tool_calls = last_message.tool_calls
    logging.info(f"---CALLING TOOLS: {[call['name'] for call in tool_calls]}---")
    
    # Create a list of coroutines for each tool call
    coroutines = []
    for call in tool_calls:
        tool_name = call['name']
        if tool_name in tools_map:
            tool_to_call = tools_map[tool_name]
            # Note: tool.ainvoke expects a dict of arguments
            coroutines.append(tool_to_call.ainvoke(call['args']))
        else:
            logging.error(f"Tool '{tool_name}' not found in tools_map.")
            # Append a placeholder for the response to maintain order
            coroutines.append(asyncio.sleep(0, result=f"Error: Tool '{tool_name}' not found."))

    try:
        # Execute all tool calls in parallel
        tool_responses = await asyncio.gather(*coroutines)
        logging.info(f"---RAW TOOL RESPONSES: {tool_responses}---")
    except Exception as e:
        logging.error(f"---ERROR DURING TOOL EXECUTION: {e}---", exc_info=True)
        error_messages = [
            ToolMessage(content=f"Error executing tool {call['name']}: {e}", tool_call_id=call["id"])
            for call in tool_calls
        ]
        return {"messages": error_messages}

    formatted_responses = []
    for call, response in zip(tool_calls, tool_responses):
        formatted_response = _format_tool_response(response)
        logging.info(f"Formatted response for tool {call['name']}: {formatted_response}")
        formatted_responses.append(
            ToolMessage(content=formatted_response, tool_call_id=call["id"])
        )
        
    logging.info(f"---FINAL FORMATTED TOOL MESSAGES: {formatted_responses}---")
    return {"messages": formatted_responses}

# The conditional edge to decide the next step
def should_continue(state):
    logging.info("---CHECKING FOR TOOL CALLS---")
    last_message = state["messages"][-1]
    logging.info(f"Last message type: {type(last_message).__name__}")
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logging.info(f"Tool calls found: {last_message.tool_calls}")
        logging.info("---DECISION: EXECUTE TOOLS---")
        return "execute_tools"
    else:
        logging.info("No tool calls found.")
        logging.info("---DECISION: END---")
        return END

# Create the agent graph
def create_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", run_agent)
    workflow.add_node("execute_tools", execute_tools)

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("execute_tools", "agent")
    
    logging.info("Agent graph created successfully.")
    return workflow.compile()

graph = create_agent_graph()