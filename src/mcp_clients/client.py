# src/mcp_clients/client.py
import json
import asyncio
from typing import Any, Dict, List, Optional
import subprocess
from dataclasses import dataclass

@dataclass
class MCPTool:
    name: str
    description: str
    parameters: Dict[str, Any]

class MCPServerClient:
    """Client for interacting with MCP servers"""
    
    def __init__(self, server_config: Dict[str, Any]):
        self.name = server_config.get("name")
        self.command = server_config.get("command", [])
        self.args = server_config.get("args", [])
        self.process: Optional[subprocess.Popen] = None
        self.tools: List[MCPTool] = []
        
    async def start(self):
        """Start the MCP server"""
        try:
            cmd = self.command + self.args
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Initialize connection and get available tools
            await self._initialize()
            
        except Exception as e:
            print(f"Error starting MCP server {self.name}: {e}")
            
    async def _initialize(self):
        """Initialize connection and discover tools"""
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "capabilities": {}
            },
            "id": 1
        }
        
        response = await self._send_request(init_request)
        if response and "result" in response:
            # Get available tools
            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 2
            }
            tools_response = await self._send_request(tools_request)
            if tools_response and "result" in tools_response:
                self.tools = [
                    MCPTool(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        parameters=tool.get("inputSchema", {})
                    )
                    for tool in tools_response["result"].get("tools", [])
                ]
    
    async def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send request to MCP server"""
        if not self.process or not self.process.stdin:
            return None
            
        try:
            # Send request
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()
            
            # Read response
            response_line = self.process.stdout.readline()
            if response_line:
                return json.loads(response_line)
                
        except Exception as e:
            print(f"Error communicating with MCP server: {e}")
            
        return None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server"""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 3
        }
        
        response = await self._send_request(request)
        if response and "result" in response:
            return response["result"]
        return None
    
    def stop(self):
        """Stop the MCP server"""
        if self.process:
            self.process.terminate()
            self.process.wait()

# MCP Server Manager
class MCPServerManager:
    """Manages multiple MCP servers"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerClient] = {}
        
    async def add_server(self, config: Dict[str, Any]):
        """Add and start an MCP server"""
        client = MCPServerClient(config)
        await client.start()
        self.servers[config["name"]] = client
        
    def get_server(self, name: str) -> Optional[MCPServerClient]:
        """Get a specific MCP server client"""
        return self.servers.get(name)
    
    def list_tools(self) -> Dict[str, List[str]]:
        """List all available tools from all servers"""
        tools = {}
        for server_name, client in self.servers.items():
            tools[server_name] = [tool.name for tool in client.tools]
        return tools
    
    def stop_all(self):
        """Stop all MCP servers"""
        for client in self.servers.values():
            client.stop()

# Example configuration for MCP servers
MCP_SERVERS_CONFIG = [
    {
        "name": "browser",
        "command": ["npx"],
        "args": ["-y", "@mcp-servers/browser"]
    },
    {
        "name": "filesystem",
        "command": ["npx"],
        "args": ["-y", "@mcp-servers/filesystem", "/tmp"]
    },
    {
        "name": "mcp-browser-use",
        "command": ["python"],
        "args": ["/home/basti/apps/npx-mcp-servers/mcp-browser-use/main.py"]
    }
]

# Integration with LangChain tools
def create_mcp_tools(manager: MCPServerManager) -> List[Tool]:
    """Create LangChain tools from MCP servers"""
    tools = []
    
    for server_name, client in manager.servers.items():
        for mcp_tool in client.tools:
            async def tool_func(args: str, server=server_name, tool=mcp_tool.name):
                try:
                    arguments = json.loads(args) if isinstance(args, str) else args
                    result = await manager.get_server(server).call_tool(tool, arguments)
                    return json.dumps(result) if result else "No result"
                except Exception as e:
                    return f"Error: {str(e)}"
            
            tools.append(Tool(
                name=f"{server_name}_{mcp_tool.name}",
                func=lambda x: asyncio.run(tool_func(x)),
                description=f"[{server_name}] {mcp_tool.description}"
            ))
    
    return tools