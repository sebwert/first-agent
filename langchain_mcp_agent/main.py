import asyncio
import os
import sys
# Optional: Set the OLLAMA host to a remote server
base_path = os.path.dirname(os.path.dirname(__file__))
sys.path.append(base_path)
from dotenv import load_dotenv
load_dotenv()

# main_with_mcp.py
import asyncio

from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent as create_langgraph_agent
# Import our MCP client
from langchain_mcp_agent.mcp_clients.client import myMCPClient
from langchain_mcp_agent.tools._model_servant import ModelServant

#langchain.debug = True

async def main():
    # Initialize Ollama
    llm = ModelServant().getModel('qwen3:30b-nothink')
    
    # Create prompt
    prompt = PromptTemplate.from_template("""
You are an AI assistant with access to multiple MCP servers and tools.

How to process user request:
Question: the input question you must answerd
Thought: think about what to do, what tools to use
Action: the action to take, must be one of tools or your own knowledge
Observation: the result of the action
... (repeat as needed)
Final Answer: the final answer

Question: {input}
Thought: {agent_scratchpad}
""")
    mcpClient = myMCPClient()
    all_tools = await mcpClient.get_tools()
    
       

    # Replace the agent creation with:
    agent_executor = create_langgraph_agent(
        model=llm.bind_tools(all_tools),  # This enables structured tool calling
        tools=all_tools
    )
    
    # Example queries
    print("\n" + "="*50)
    print("Agent ready! Testing with example queries...")
    print("="*50)
    
    queries = [
        "Look up how many continents there are on Earth",
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-"*30)
        try:
            result =  await agent_executor.ainvoke({"messages": [
                SystemMessage(content="You are an AI assistant with access to multiple MCP servers."),
                HumanMessage(content=query)
            ]})
            print(f"Result: {result['output']}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Interactive mode
    print("\n" + "="*50)
    print("Interactive mode - type 'exit' to quit")
    print("="*50)
    # Cleanup
    print("\nShutting down MCP servers...")
    #mcp_manager.stop_all()

if __name__ == "__main__":
    asyncio.run(main())