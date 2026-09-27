from app import create_server
from app.config import Config

if __name__ == "__main__":
    mcp = create_server()
    mcp.run(
        transport="streamable-http",
        host=Config.MCP_SERVER_HOST,
        port=Config.MCP_SERVER_PORT,
    )
