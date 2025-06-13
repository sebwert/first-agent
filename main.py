# main_with_mcp.py
import asyncio
import os
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate

# Import our MCP client
from src.mcp_clients.client import MCPServerManager, MCP_SERVERS_CONFIG, create_mcp_tools

# Load environment variables
load_dotenv()

async def main():
    # Initialize Ollama
    llm = ChatOllama(
        model="llama3.2",
        temperature=0,
        base_url="http://localhost:11434"
    )
    
    # Initialize MCP Server Manager
    mcp_manager = MCPServerManager()
    
    # Start MCP servers
    print("Starting MCP servers...")
    for config in MCP_SERVERS_CONFIG:
        try:
            await mcp_manager.add_server(config)
            print(f"✓ Started {config['name']}")
        except Exception as e:
            print(f"✗ Failed to start {config['name']}: {e}")
    
    # Get tools from MCP servers
    mcp_tools = create_mcp_tools(mcp_manager)
    
    # Additional custom tools
    @tool
    def list_mcp_servers() -> str:
        """List all available MCP servers and their tools"""
        tools_by_server = mcp_manager.list_tools()
        result = []
        for server, tools in tools_by_server.items():
            result.append(f"{server}: {', '.join(tools)}")
        return "\n".join(result)
    
    # Combine all tools
    all_tools = mcp_tools + [list_mcp_servers]
    
    # Create prompt
    prompt = PromptTemplate.from_template("""
You are an AI assistant with access to multiple MCP servers and tools.

Available tools:
{tools}

Use this format:
Question: the input question you must answer
Thought: think about what to do
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action (for MCP tools, use JSON format)
Observation: the result of the action
... (repeat as needed)
Thought: I now know the final answer
Final Answer: the final answer

Question: {input}
Thought: {agent_scratchpad}
""")
    
    # Create agent
    agent = create_react_agent(
        llm=llm,
        tools=all_tools,
        prompt=prompt
    )
    
    # Create executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=all_tools,
        verbose=True,
        handle_parsing_errors=True
    )
    
    # Example queries
    print("\n" + "="*50)
    print("Agent ready! Testing with example queries...")
    print("="*50)
    
    queries = [
        "List all available MCP servers and their tools",
        "Use the browser to navigate to example.com",
        "List files in /tmp directory"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-"*30)
        try:
            result = agent_executor.invoke({"input": query})
            print(f"Result: {result['output']}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Interactive mode
    print("\n" + "="*50)
    print("Interactive mode - type 'exit' to quit")
    print("="*50)
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
            
        try:
            result = agent_executor.invoke({"input": user_input})
            print(f"\nAgent: {result['output']}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Cleanup
    print("\nShutting down MCP servers...")
    mcp_manager.stop_all()

if __name__ == "__main__":
    asyncio.run(main())