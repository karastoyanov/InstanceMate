import click
from flask import Flask, current_app

from app.services import mcp_client


def register_cli(app: Flask) -> None:
    @app.cli.command("mcp-check")
    def mcp_check() -> None:
        """Check the backend can reach the MCP server: list its tools and
        call `ping`. Needs the MCP server running at MCP_SERVER_URL."""
        click.echo(f"MCP server: {current_app.config.get('MCP_SERVER_URL')}")

        try:
            tools = mcp_client.list_tools()
        except mcp_client.McpUnavailableError as exc:
            raise click.ClickException(str(exc)) from exc

        names = ", ".join(tool["function"]["name"] for tool in tools)
        click.echo(f"Tools: {names}")

        result = mcp_client.call_tool("ping")
        if result.is_error:
            raise click.ClickException(f"ping failed: {result.content}")
        click.echo(f"ping -> {result.content}")
