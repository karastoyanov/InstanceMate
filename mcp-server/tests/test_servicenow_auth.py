import asyncio

from app.servicenow_auth import SERVICENOW_META_KEY, get_servicenow_credentials
from mcp import Client
from mcp.server.mcpserver import Context, MCPServer


def _server_echoing_credentials() -> MCPServer:
    mcp = MCPServer("test")

    @mcp.tool()
    def whoami(ctx: Context) -> str:
        credentials = get_servicenow_credentials(ctx)
        return credentials["instance_url"] if credentials else "anonymous"

    return mcp


def _call_whoami(meta: dict | None) -> str:
    async def run() -> str:
        async with Client(_server_echoing_credentials()) as client:
            result = await client.call_tool("whoami", {}, meta=meta)
            return result.content[0].text

    return asyncio.run(run())


def test_reads_credentials_from_request_meta():
    meta = {
        SERVICENOW_META_KEY: {
            "instance_url": "https://dev12345.service-now.com",
            "auth_type": "oauth",
            "access_token": "the-token",
        }
    }
    assert _call_whoami(meta) == "https://dev12345.service-now.com"


def test_returns_none_without_credentials():
    assert _call_whoami(None) == "anonymous"
