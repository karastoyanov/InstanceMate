"""Per-call ServiceNow credentials, passed in by the backend (#22).

This server holds no per-user state: on every tool call the backend puts
the caller's ServiceNow credentials in the request's `_meta` under
SERVICENOW_META_KEY (see backend/app/services/mcp_client.py - keep the
two in sync). Tools that talk to ServiceNow read them with
get_servicenow_credentials(ctx), so they never appear in the tool
arguments the LLM sees or writes.

The shape is:
    {"instance_url": ..., "auth_type": "oauth", "access_token": ...}
or
    {"instance_url": ..., "auth_type": "basic", "username": ..., "password": ...}
"""

from typing import Any

from mcp.server.mcpserver import Context

SERVICENOW_META_KEY = "instancemate/servicenow"


def get_servicenow_credentials(ctx: Context) -> dict[str, Any] | None:
    """The caller's ServiceNow credentials for this tool call, or None if
    the backend didn't send any."""
    meta = ctx.request_context.meta or {}
    credentials = meta.get(SERVICENOW_META_KEY)
    return credentials if isinstance(credentials, dict) else None
