"""Backend side of the backend <-> MCP server wiring (#22).

Lists the MCP server's tools in the shape LiteLLM's tool-calling API
expects (#21), and calls one by name on the LLM's behalf. The MCP server
holds no per-user state, so the caller's ServiceNow credentials (from
their ServiceNowProfile - #39) go along with every tool call in the
request's `_meta`, never in the tool arguments the LLM sees or writes.

Flask is synchronous, so each public function opens a short-lived MCP
connection, does its one job and closes it again.
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
    react to them instead of the request crashing."""

    content: str
    is_error: bool = False


def list_tools(server: McpTarget | None = None) -> list[dict]:
    """The MCP server's tools, converted for LiteLLM's `tools=` argument.

    Raises McpUnavailableError if the server can't be reached - without
    tools there's nothing for the LLM to call, so the caller decides
    whether to carry on without them.
    """
    try:
        tools = asyncio.run(_list_tools(_resolve_target(server)))
    except McpUnavailableError:
        raise
    except Exception as exc:
        logger.warning("Could not list MCP tools", exc_info=True)
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

    Never raises: an unreachable server, a missing tool or a failing tool
    all come back as an error ToolResult for the LLM to see.
    """
    meta = None
    if profile is not None:
        try:
            meta = {SERVICENOW_META_KEY: servicenow_credentials_meta(profile)}
        except ServiceNowCredentialsError as exc:
            return ToolResult(str(exc), is_error=True)

    try:
        target = _resolve_target(server)
    except McpUnavailableError as exc:
        return ToolResult(str(exc), is_error=True)

    try:
        result = asyncio.run(_call_tool(target, name, arguments or {}, meta))
    except MCPError as exc:
        # The server answered, but refused the call (unknown tool, invalid
        # arguments, ...) - its message is meant for the caller.
        return ToolResult(exc.error.message, is_error=True)
    except Exception:
        logger.warning("MCP tool call %r failed", name, exc_info=True)
        return ToolResult(_UNREACHABLE_MESSAGE, is_error=True)

    return ToolResult(_result_text(result), is_error=result.is_error)


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

    Raises ServiceNowCredentialsError if an OAuth token can't be refreshed.
    """
    meta = {"instance_url": profile.instance_url, "auth_type": profile.auth_type}

    if profile.auth_type == "oauth":
        access_token = servicenow_profile_service.get_valid_access_token(profile)
        if access_token is None:
            raise ServiceNowCredentialsError(
                "The ServiceNow connection has expired. Reconnect this "
                "ServiceNow profile in Settings and try again."
            )
        meta["access_token"] = access_token
    else:
        credentials = servicenow_profile_service.get_credentials(profile)
        meta["username"] = credentials["username"]
        meta["password"] = credentials["password"]

    return meta


def _resolve_target(server: McpTarget | None) -> McpTarget:
    target = server if server is not None else current_app.config.get("MCP_SERVER_URL")
    if not target:
        raise McpUnavailableError("The tool server is not configured (MCP_SERVER_URL).")
    return target


async def _list_tools(target: McpTarget) -> list[Tool]:
    async with Client(target) as client:
        tools: list[Tool] = []
        cursor = None
        while True:
            page = await client.list_tools(cursor=cursor)
            tools.extend(page.tools)
            cursor = page.next_cursor
            if cursor is None:
                return tools


async def _call_tool(
    target: McpTarget, name: str, arguments: dict, meta: dict | None
) -> CallToolResult:
    async with Client(target) as client:
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
