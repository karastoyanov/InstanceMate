import asyncio
import socket
import threading
import time
from unittest.mock import patch

import pytest
from app.extensions import db
from app.models.user import User
from app.services import mcp_client, servicenow_profile_service
from app.services.mcp_client import SERVICENOW_META_KEY, McpUnavailableError
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from werkzeug.security import generate_password_hash

INSTANCE_URL = "https://dev12345.service-now.com"
# Nothing listens on port 9 (discard) - stands in for a down MCP server.
UNREACHABLE_URL = "http://127.0.0.1:9/mcp"


@pytest.fixture
def mcp_server() -> MCPServer:
    """In-process stand-in for the real MCP server (whose `app` package
    can't be imported here - it collides with the backend's)."""
    mcp = MCPServer("test")

    @mcp.tool()
    def ping() -> str:
        """Check that the MCP server is reachable and responding."""
        return "pong"

    @mcp.tool()
    def echo_credentials(ctx: Context) -> dict:
        """Return the ServiceNow credentials this call was made with."""
        return (ctx.request_context.meta or {}).get(SERVICENOW_META_KEY) or {}

    @mcp.tool()
    def lookup(table: str, limit: int = 10) -> str:
        """Look something up."""
        raise ToolError(f"no such table: {table}")

    return mcp


def _make_user() -> User:
    user = User(
        email="jane@example.com",
        username="jane_doe",
        password_hash=generate_password_hash("correct-horse-battery"),
    )
    db.session.add(user)
    db.session.commit()
    return user


def _basic_profile():
    return servicenow_profile_service.create_basic_profile(
        _make_user().id, "Acme Dev", INSTANCE_URL, "admin", "super-secret"
    )


def _oauth_profile(expires_in: int = 3600, refresh_token: str | None = "refresh"):
    return servicenow_profile_service.create_oauth_profile(
        _make_user().id,
        "Acme Prod",
        INSTANCE_URL,
        "abc123",
        "client-secret",
        {
            "access_token": "the-token",
            "refresh_token": refresh_token,
            "expires_in": expires_in,
        },
    )


def test_list_tools_converts_to_llm_function_tools(app, mcp_server):
    tools = {t["function"]["name"]: t for t in mcp_client.list_tools(mcp_server)}

    assert tools["ping"] == {
        "type": "function",
        "function": {
            "name": "ping",
            "description": "Check that the MCP server is reachable and responding.",
            "parameters": {"type": "object", "properties": {}},
        },
    }
    lookup = tools["lookup"]["function"]["parameters"]
    assert lookup["required"] == ["table"]
    assert set(lookup["properties"]) == {"table", "limit"}


def test_list_tools_raises_when_server_unreachable(app):
    with pytest.raises(McpUnavailableError):
        mcp_client.list_tools(UNREACHABLE_URL)


def test_list_tools_raises_when_not_configured(app):
    app.config["MCP_SERVER_URL"] = None
    with pytest.raises(McpUnavailableError):
        mcp_client.list_tools()


def test_call_tool_returns_text_result(app, mcp_server):
    result = mcp_client.call_tool("ping", {}, server=mcp_server)
    assert result == mcp_client.ToolResult("pong", is_error=False)


def test_call_tool_uses_configured_server_by_default(app, mcp_server):
    app.config["MCP_SERVER_URL"] = mcp_server
    assert mcp_client.call_tool("ping").content == "pong"


def test_call_tool_passes_basic_credentials_in_meta(app, mcp_server):
    profile = _basic_profile()

    result = mcp_client.call_tool(
        "echo_credentials", {}, profile=profile, server=mcp_server
    )

    assert result.is_error is False
    assert '"username": "admin"' in result.content
    assert '"password": "super-secret"' in result.content
    assert INSTANCE_URL in result.content


def test_call_tool_passes_live_oauth_token_in_meta(app, mcp_server):
    profile = _oauth_profile()

    result = mcp_client.call_tool(
        "echo_credentials", {}, profile=profile, server=mcp_server
    )

    assert '"access_token": "the-token"' in result.content
    assert "client-secret" not in result.content
    assert "refresh" not in result.content


def test_call_tool_refreshes_expired_oauth_token_first(app, mcp_server):
    profile = _oauth_profile(expires_in=0)

    with patch(
        "app.services.servicenow_profile_service.servicenow_oauth.refresh_access_token",
        return_value={"access_token": "fresh-token", "expires_in": 3600},
    ):
        result = mcp_client.call_tool(
            "echo_credentials", {}, profile=profile, server=mcp_server
        )

    assert '"access_token": "fresh-token"' in result.content


def test_call_tool_with_expired_unrefreshable_oauth_is_tool_error(app, mcp_server):
    profile = _oauth_profile(expires_in=0, refresh_token=None)

    result = mcp_client.call_tool(
        "echo_credentials", {}, profile=profile, server=mcp_server
    )

    assert result.is_error is True
    assert "Reconnect" in result.content


def test_call_tool_failing_tool_is_tool_error(app, mcp_server):
    result = mcp_client.call_tool("lookup", {"table": "nope"}, server=mcp_server)

    assert result.is_error is True
    assert "no such table: nope" in result.content


def test_call_tool_unknown_tool_is_tool_error(app, mcp_server):
    result = mcp_client.call_tool("does_not_exist", {}, server=mcp_server)

    assert result.is_error is True
    assert "does_not_exist" in result.content


def test_call_tool_unreachable_server_is_tool_error(app):
    start = time.monotonic()
    result = mcp_client.call_tool("ping", {}, server=UNREACHABLE_URL)

    assert result.is_error is True
    assert (
        result.content
        == "Error: The tool server is unreachable right now. Try again later."
    )
    assert time.monotonic() - start < 30


def test_call_tool_unreachable_server_does_not_leak_credentials(app):
    profile = _basic_profile()

    result = mcp_client.call_tool("ping", {}, profile=profile, server=UNREACHABLE_URL)

    assert result.is_error is True
    assert "super-secret" not in result.content


@pytest.fixture
def silent_server_url():
    """A server that accepts connections but never answers."""
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    accepted = []

    def accept_forever():
        while True:
            try:
                conn, _ = listener.accept()
            except OSError:
                return
            accepted.append(conn)

    threading.Thread(target=accept_forever, daemon=True).start()
    yield f"http://127.0.0.1:{listener.getsockname()[1]}/mcp"
    listener.close()
    for conn in accepted:
        conn.close()


def _break_decryption(app):
    # Simulates a rotated SESSION_SECRET: stored credentials no longer decrypt.
    app.config["SESSION_SECRET"] = "a-different-secret"


def test_error_results_start_with_error_prefix(app, mcp_server):
    result = mcp_client.call_tool("lookup", {"table": "nope"}, server=mcp_server)
    assert result.content.startswith(mcp_client.ERROR_PREFIX)

    ok = mcp_client.call_tool("ping", {}, server=mcp_server)
    assert not ok.content.startswith(mcp_client.ERROR_PREFIX)


def test_call_tool_basic_profile_with_undecryptable_credentials(app, mcp_server):
    profile = _basic_profile()
    _break_decryption(app)

    result = mcp_client.call_tool("ping", {}, profile=profile, server=mcp_server)

    assert result.is_error is True
    assert "Reconnect" in result.content


def test_call_tool_oauth_profile_with_undecryptable_credentials(app, mcp_server):
    profile = _oauth_profile()
    _break_decryption(app)

    result = mcp_client.call_tool("ping", {}, profile=profile, server=mcp_server)

    assert result.is_error is True
    assert "Reconnect" in result.content


def test_call_tool_unknown_auth_type_is_tool_error(app, mcp_server):
    profile = _basic_profile()
    profile.auth_type = "saml"

    result = mcp_client.call_tool("ping", {}, profile=profile, server=mcp_server)

    assert result.is_error is True
    assert "saml" in result.content


def test_call_tool_not_configured_skips_oauth_refresh(app):
    app.config["MCP_SERVER_URL"] = None
    profile = _oauth_profile(expires_in=0)

    with patch(
        "app.services.servicenow_profile_service.servicenow_oauth.refresh_access_token"
    ) as mock_refresh:
        result = mcp_client.call_tool("ping", {}, profile=profile)

    assert result.is_error is True
    mock_refresh.assert_not_called()


def test_call_tool_times_out_on_silent_server(app, silent_server_url):
    app.config["MCP_TIMEOUT_SECONDS"] = 1

    start = time.monotonic()
    result = mcp_client.call_tool("ping", {}, server=silent_server_url)

    assert result.is_error is True
    assert time.monotonic() - start < 5


def test_list_tools_times_out_on_silent_server(app, silent_server_url):
    app.config["MCP_TIMEOUT_SECONDS"] = 1

    start = time.monotonic()
    with pytest.raises(McpUnavailableError):
        mcp_client.list_tools(silent_server_url)
    assert time.monotonic() - start < 5


def test_call_from_running_event_loop_raises(app, mcp_server):
    async def call_inside_loop():
        mcp_client.call_tool("ping", {}, server=mcp_server)

    with pytest.raises(RuntimeError, match="synchronous code"):
        asyncio.run(call_inside_loop())


def test_list_tools_from_running_event_loop_raises(app, mcp_server):
    async def call_inside_loop():
        mcp_client.list_tools(mcp_server)

    with pytest.raises(RuntimeError, match="synchronous code"):
        asyncio.run(call_inside_loop())
