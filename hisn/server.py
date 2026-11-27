
"""MCP server exposing Hisn's three SOC tools."""

from mcp.server import MCPServer

from hisn.tools import (
    lookup_asset as lookup_asset_tool,
    related_alerts as related_alerts_tool,
    search_runbooks as search_runbooks_tool,
)


# Create the MCP server.
server = MCPServer("hisn-triage")


@server.tool()
def lookup_asset(host: str) -> dict:
    """Look up an asset by hostname, including its owner and criticality."""
    return lookup_asset_tool(host)


@server.tool()
def search_runbooks(query: str, k: int = 3) -> list[dict]:
    """Search the SOC runbooks and return the most relevant matches."""
    return search_runbooks_tool(query, k)


@server.tool()
def related_alerts(
    rule_id: str,
    agent: str,
    around: str,
    window_minutes: int = 60,
) -> dict:
    """Count related alerts matching a rule and agent within a time window."""
    return related_alerts_tool(
        rule_id,
        agent,
        around,
        window_minutes,
    )


if __name__ == "__main__":
    server.run()
