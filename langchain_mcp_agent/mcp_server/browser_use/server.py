import asyncio
import os
import sys
# Optional: Set the OLLAMA host to a remote server
base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_path)
from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP
from langchain_mcp_agent.mcp_server.browser_use.bu_easy_agent import BUEasyAgent

def serve() -> FastMCP:
    server = FastMCP("browser-use")

    @server.tool(description="Search for the boiling point of water at sea level")
    async def web_research(task: str) -> str:
        """Research the web for the given task abd get the result of the research"""
        #print("🔨 mcp server browser-use web_research triggered")
        try:
            agent = BUEasyAgent(enable_memory=False)
            result = await agent.run_search(task)
            report_content = f"Result of web research is: {result}"
        except Exception as e:
            report_content = f"Error: {e}"
        return report_content
    
    return server
    
server_instance = serve() # Renamed from 'server' to avoid conflict with 'settings.server'

if __name__ == "__main__":
    #print("🔨 mcp server browser-use started")
    server_instance.run()