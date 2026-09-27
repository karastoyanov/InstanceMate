from mcp.server.mcpserver import MCPServer

from app.tools import register_tools


def create_server() -> MCPServer:
    mcp = MCPServer("InstanceMate MCP Server")
    register_tools(mcp)
    return mcp
