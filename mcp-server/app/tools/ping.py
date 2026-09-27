from mcp.server.mcpserver import MCPServer


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    def ping() -> str:
        """Check that the MCP server is reachable and responding."""
        return "pong"
