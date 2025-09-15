import asyncio
import logging
from langchain_mcp_adapters.client import MultiServerMCPClient
from financial_agent.mcp_config.config import load_mcp_config
from financial_agent.graph import create_agent_graph
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.utils.function_calling import convert_to_openai_tool
from langgraph.prebuilt import ToolNode
import os
from dotenv import load_dotenv
from .llm import ChatOpenRouter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

async def main():
    server_configs = load_mcp_config()
    processes = []

    try:
        logging.info("Starting MCP servers...")
        for server_name, config in server_configs["mcpServers"].items():
            env = os.environ.copy()
            if "env" in config:
                env.update(config["env"])

            command_str = " ".join([config["command"]] + config["args"])
            process = await asyncio.create_subprocess_shell(command_str, env=env)
            processes.append(process)
            logging.info(f"Started MCP server '{server_name}' with PID {process.pid}")

        logging.info("Waiting for servers to initialize...")
        await asyncio.sleep(5)

        client_config = server_configs["mcpServers"]
        for server_name, config in client_config.items():
            if "transport" not in config:
                config["transport"] = "stdio"

        tool_executor = MultiServerMCPClient(client_config)
        tools = await tool_executor.get_tools()
        logging.info(f"Available tools: {[tool.name for tool in tools]}")

        tools_for_llm = [convert_to_openai_tool(tool) for tool in tools]
        tools_map = {tool.name: tool for tool in tools}

        llm = ChatOpenRouter(
            model_name=os.environ.get("OPENROUTER_MODEL", "google/gemini-flash-1.5:free"),
        )
        
        app = create_agent_graph()

        logging.info("Agentic Chatbot is ready. Type 'exit' to end the conversation.")
        
        conversation_history = []

        while True:
            logging.info("Waiting for user input...")
            user_input = (await asyncio.to_thread(input, "You: ")).strip()
            logging.info(f"User input received: '{user_input}'")

            if user_input.lower() == "exit":
                logging.info("Exit command received. Shutting down.")
                break

            if not user_input:
                logging.warning("Empty input received. Please enter a message.")
                continue

            conversation_history.append(HumanMessage(content=user_input))
            logging.info(f"Appended to history. New history length: {len(conversation_history)}")

            config = {
                "configurable": {
                    "llm": llm,
                    "tools": tools_for_llm,
                    "tools_map": tools_map,
                }
            }
            
            inputs = {"messages": conversation_history}
            logging.info(f"Streaming graph with inputs: {inputs}")
            
            final_state = None
            try:
                final_state = await app.ainvoke(inputs, config=config)
                logging.info(f"---GRAPH FINAL STATE: {final_state}---")
            except Exception as e:
                logging.error(f"---ERROR DURING GRAPH INVOCATION: {e}---", exc_info=True)
                continue

            if final_state:
                conversation_history = final_state.get("messages", [])
                logging.info(f"Graph execution finished. Final history length: {len(conversation_history)}")
                last_message = conversation_history[-1] if conversation_history else None
                
                if isinstance(last_message, AIMessage) and not last_message.tool_calls:
                    logging.info(f"Final response from bot: {last_message.content}")
                    print("Bot:", last_message.content)
                else:
                    logging.info("No final message from bot to display.")
            else:
                logging.warning("Graph execution returned no final state.")

    finally:
        logging.info("Terminating all MCP servers...")
        for process in processes:
            try:
                process.terminate()
                await process.wait()
                logging.info(f"Terminated MCP server with PID {process.pid}")
            except ProcessLookupError:
                logging.warning(f"Process with PID {process.pid} already terminated.")
        logging.info("All MCP servers have been shut down.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Exiting.")