"""Backend side of the backend <-> MCP server wiring (#22).

Lists the MCP server's tools in the shape LiteLLM's tool-calling API
expects (#21), and calls one by name on the LLM's behalf. The MCP server
holds no per-user state, so the caller's ServiceNow credentials (from
their ServiceNowProfile - #39) go along with every tool call in the
request's `_meta`, never in the tool arguments the LLM sees or writes.

Flask is synchronous, so each public function opens a short-lived MCP
connection, does its one job and closes it again. They must be called
from synchronous code, not from inside a running event loop.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

from flask import current_app
from mcp import Client
from mcp.server.mcpserver import MCPServer
from mcp.shared.exceptions import MCPError
from mcp_types import CallToolResult, TextContent, Tool

from app.models.servicenow_profile import ServiceNowProfile
from app.services import servicenow_profile_service

logger = logging.getLogger(__name__)

# `_meta` key the MCP server reads the caller's ServiceNow credentials from
# (see mcp-server/app/servicenow_auth.py) - keep the two in sync.
SERVICENOW_META_KEY = "instancemate/servicenow"

# What the LLM sees when the MCP server can't be reached - deliberately
# generic, so connection details never end up in the conversation.
_UNREACHABLE_MESSAGE = "The tool server is unreachable right now. Try again later."
_RECONNECT_MESSAGE = (
    "The ServiceNow connection has expired. Reconnect this ServiceNow "
    "profile in Settings and try again."
)

# Either a URL (the real server) or an in-process server (tests).
McpTarget = str | MCPServer


class McpUnavailableError(Exception):
    """Raised when the MCP server can't be reached or isn't configured."""


class ServiceNowCredentialsError(Exception):
    """Raised when a profile has no usable ServiceNow credentials."""


@dataclass
class ToolResult:
    """Outcome of one tool call, ready to send back to the LLM as a tool
    message. Failures are results too (is_error=True), so the LLM can
    react to them instead of the request crashing.

    The OpenAI-style tool message LiteLLM sends has no error flag, so the
    content of an error result always starts with ERROR_PREFIX - that is
    how the LLM tells it apart from a successful result.
    """

    content: str
    is_error: bool = False


ERROR_PREFIX = "Error: "


def _error(message: str) -> ToolResult:
    return ToolResult(ERROR_PREFIX + message, is_error=True)


def list_tools(server: McpTarget | None = None) -> list[dict]:
    """The MCP server's tools, converted for LiteLLM's `tools=` argument.

    Raises McpUnavailableError if the server can't be reached - without
    tools there's nothing for the LLM to call, so the caller decides
    whether to carry on without them.
    """
    _ensure_no_running_loop()
    target = _resolve_target(server)
    try:
        tools = asyncio.run(_list_tools(target, _timeout()))
    except Exception as exc:
        logger.warning(
            "Could not list MCP tools (%s)", type(exc).__name__, exc_info=True
        )
        raise McpUnavailableError(_UNREACHABLE_MESSAGE) from exc
    return [to_llm_tool(tool) for tool in tools]


def call_tool(
    name: str,
    arguments: dict[str, Any] | None = None,
    profile: ServiceNowProfile | None = None,
    server: McpTarget | None = None,
) -> ToolResult:
    """Call one MCP tool by name, passing `profile`'s ServiceNow credentials
    through so the tool can act as the caller.

    An unconfigured or unreachable server, unusable credentials, a missing
    tool or a failing tool all come back as an error ToolResult for the
    LLM to see. The only exception is a RuntimeError when this is called
    from inside a running event loop - that is a bug in the caller.
    """
    _ensure_no_running_loop()

    # Resolve the server first: refreshing an OAuth token is wasted work
    # when the call can't be made anyway.
    try:
        target = _resolve_target(server)
    except McpUnavailableError as exc:
        return _error(str(exc))

    meta = None
    if profile is not None:
        try:
            meta = {SERVICENOW_META_KEY: servicenow_credentials_meta(profile)}
        except ServiceNowCredentialsError as exc:
            return _error(str(exc))

    try:
        result = asyncio.run(
            _call_tool(target, name, arguments or {}, meta, _timeout())
        )
    except MCPError as exc:
        # The server answered, but refused the call (unknown tool, invalid
        # arguments, ...) - its message is meant for the caller.
        return _error(exc.error.message)
    except Exception as exc:
        logger.warning(
            "MCP tool call %r failed (%s)", name, type(exc).__name__, exc_info=True
        )
        return _error(_UNREACHABLE_MESSAGE)

    text = _result_text(result)
    return _error(text) if result.is_error else ToolResult(text)


def to_llm_tool(tool: Tool) -> dict:
    """Convert one MCP tool definition to the OpenAI-style function tool
    LiteLLM accepts for every provider."""
    parameters = dict(tool.input_schema)
    parameters.setdefault("type", "object")
    parameters.setdefault("properties", {})
    # Pydantic's generated title ("pingArguments") is noise to the LLM.
    parameters.pop("title", None)

    function: dict[str, Any] = {"name": tool.name, "parameters": parameters}
    if tool.description:
        function["description"] = tool.description
    return {"type": "function", "function": function}


def servicenow_credentials_meta(profile: ServiceNowProfile) -> dict:
    """The credentials the MCP server needs to call ServiceNow as this
    profile. OAuth profiles get a live access token (refreshed first if
    needed), basic-auth profiles their username/password.

    Raises ServiceNowCredentialsError if the stored credentials can't be
    decrypted (e.g. SESSION_SECRET was rotated), an OAuth token can't be
    refreshed, or the profile has an unknown auth type.
    """
    meta = {"instance_url": profile.instance_url, "auth_type": profile.auth_type}

    if profile.auth_type == "oauth":
        access_token = servicenow_profile_service.get_valid_access_token(profile)
        if access_token is None:
            raise ServiceNowCredentialsError(_RECONNECT_MESSAGE)
        meta["access_token"] = access_token
    elif profile.auth_type == "basic":
        credentials = servicenow_profile_service.get_credentials(profile)
        if credentials is None:
            raise ServiceNowCredentialsError(_RECONNECT_MESSAGE)
        meta["username"] = credentials["username"]
        meta["password"] = credentials["password"]
    else:
        raise ServiceNowCredentialsError(
            f"Unsupported ServiceNow auth type: {profile.auth_type!r}."
        )

    return meta


def _resolve_target(server: McpTarget | None) -> McpTarget:
    target = server if server is not None else current_app.config.get("MCP_SERVER_URL")
    if not target:
        raise McpUnavailableError("The tool server is not configured (MCP_SERVER_URL).")
    return target


def _ensure_no_running_loop() -> None:
    # asyncio.run() fails inside a running loop (an async route, an asyncio
    # worker). Raise that here, outside the catch-alls, so it shows up as
    # the caller bug it is - not as "tool server is unreachable".
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return
    raise RuntimeError(
        "mcp_client must be called from synchronous code, not from inside "
        "a running event loop."
    )


def _timeout() -> float:
    return current_app.config["MCP_TIMEOUT_SECONDS"]


async def _list_tools(target: McpTarget, timeout: float) -> list[Tool]:
    # One deadline for the whole operation (connect, handshake, requests):
    # without it, a server that accepts the connection but never answers
    # ties up a worker for minutes, and the SDK's protocol probe alone has
    # its own fixed 10 s timeout.
    async with asyncio.timeout(timeout), Client(target) as client:
        tools: list[Tool] = []
        cursor = None
        while True:
            page = await client.list_tools(cursor=cursor)
            tools.extend(page.tools)
            cursor = page.next_cursor
            if cursor is None:
                return tools


async def _call_tool(
    target: McpTarget, name: str, arguments: dict, meta: dict | None, timeout: float
) -> CallToolResult:
    # Same single deadline as _list_tools.
    async with asyncio.timeout(timeout), Client(target) as client:
        return await client.call_tool(name, arguments, meta=meta)


def _result_text(result: CallToolResult) -> str:
    parts = []
    for block in result.content:
        if isinstance(block, TextContent):
            parts.append(block.text)
        else:
            parts.append(json.dumps(block.model_dump(mode="json", exclude_none=True)))
    if not parts and result.structured_content is not None:
        parts.append(json.dumps(result.structured_content))
    return "\n".join(parts)
