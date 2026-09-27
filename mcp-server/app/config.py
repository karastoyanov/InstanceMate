import os


class Config:
    """Placeholder ServiceNow auth config.

    Real per-user ServiceNow authentication is handled by the backend (see
    #8 OAuth, #9 basic auth, #10 session management). Once real ServiceNow
    tools exist here, the backend will pass the caller's credentials
    through on each tool call rather than this server holding its own
    session - these env vars only exist for manually exercising a future
    tool against a single fixed instance during local development.
    """

    SERVICENOW_INSTANCE_URL = os.environ.get("SERVICENOW_INSTANCE_URL")
    SERVICENOW_ACCESS_TOKEN = os.environ.get("SERVICENOW_ACCESS_TOKEN")

    MCP_SERVER_HOST = os.environ.get("MCP_SERVER_HOST", "127.0.0.1")
    MCP_SERVER_PORT = int(os.environ.get("MCP_SERVER_PORT", "8001"))
