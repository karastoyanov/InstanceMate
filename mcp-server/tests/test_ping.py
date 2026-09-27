import asyncio


def test_ping_is_registered(mcp):
    tools = asyncio.run(mcp.list_tools())
    names = [tool.name for tool in tools]
    assert "ping" in names


def test_ping_returns_pong(mcp):
    result = asyncio.run(mcp.call_tool("ping", {}))
    assert result.is_error is False
    assert result.content[0].text == "pong"
