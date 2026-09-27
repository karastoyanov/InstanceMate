from mcp.server.mcpserver import MCPServer

from app.tools.ping import register as register_ping


def register_tools(mcp: MCPServer) -> None:
    register_ping(mcp)
