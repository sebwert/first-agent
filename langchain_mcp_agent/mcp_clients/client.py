import asyncio
import os
import sys
# Optional: Set the OLLAMA host to a remote server
base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(base_path)
from dotenv import load_dotenv
load_dotenv()

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
from langchain_core.tools import BaseTool

class myMCPClient:    
    def __init__(self):
        self.connection_string = os.getenv("MCP_MONGODB_CONNECTION_STRING")
        self.client_config = {
            "mongodb": {
                "command": "node",
                "args": [os.getenv("MCP_MONGODB_SERVER_PATH"),
                        "--connectionString", os.getenv("MCP_MONGODB_CONNECTION_STRING")],
                "transport": "stdio",
            },
            "browser-use": {
                "command": "uv",
                "args": [
                    "--directory", base_path, "run", "python",
                    f"{base_path}/langchain_mcp_agent/mcp_server/browser_use/server.py"
                ],
                "env": {
                    "MCP_LLM_PROVIDER": os.getenv("MCP_BROWSER_USE_LLM_PROVIDER"),
                    "MCP_LLM_MODEL_NAME": os.getenv("MCP_BROWSER_USE_LLM_MODEL_NAME"),
                    "MCP_LLM_OLLAMA_NUM_CTX": os.getenv("MCP_BROWSER_USE_LLM_OLLAMA_NUM_CTX"),
                    "MCP_LLM_TEMPERATURE": os.getenv("MCP_BROWSER_USE_LLM_TEMPERATURE"),
                    "MCP_LLM_BASE_URL": os.getenv("MCP_BROWSER_USE_LLM_BASE_URL"),
                    "MCP_BROWSER_HEADLESS": os.getenv("MCP_BROWSER_USE_BROWSER_HEADLESS"),
                    "MCP_BROWSER_WINDOW_WIDTH": os.getenv("MCP_BROWSER_USE_BROWSER_WINDOW_WIDTH"),
                    "MCP_AGENT_TOOL_MAX_INPUT_TOKENS": os.getenv("MCP_BROWSER_USE_AGENT_TOOL_MAX_INPUT_TOKENS"),
                    "MCP_SERVER_LOGGING_LEVEL": os.getenv("MCP_BROWSER_USE_SERVER_LOGGING_LEVEL"),
                    "ANONYMIZED_TELEMETRY": os.getenv("ANONYMIZED_TELEMETRY", "false"),
                    "MCP_LLM_OLLAMA_NUM_PREDICT": os.getenv("MCP_BROWSER_USE_LLM_OLLAMA_NUM_PREDICT"),
                },
                "transport": "stdio",
            }
        }
    
    async def get_tools(self) -> list[BaseTool]:
        # Initialize LangChain MCP integration
        client = MultiServerMCPClient(self.client_config)
        tools: list[BaseTool] = await client.get_tools()
        return tools
        
    