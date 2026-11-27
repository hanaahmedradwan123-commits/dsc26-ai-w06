
"""Hisn's three tools: asset lookup, runbook search, related-alert count."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from hisn.retrieval import search_runbooks


__all__ = [
    "lookup_asset",
    "related_alerts",
    "search_runbooks",
    "TOOLS",
    "TOOL_SCHEMAS",
]

DATA_DIR = Path(__file__).parent / "data"
ASSETS_FILE = DATA_DIR / "assets.json"
ALERTS_FILE = DATA_DIR / "alerts.jsonl"


def lookup_asset(host: str) -> dict:
    """Look up an asset by hostname, ignoring case and surrounding spaces."""

    with ASSETS_FILE.open("r", encoding="utf-8") as file:
        assets = json.load(file)

    normalized_host = host.strip().casefold()

    for asset in assets:
        if asset["host"].casefold() == normalized_host:
            return {**asset, "known": True}

    return {"host": host, "known": False}


def related_alerts(
    rule_id: str,
    agent: str,
    around: str,
    window_minutes: int = 60,
) -> dict:
    """Count matching alerts within an inclusive time window."""

    if (
        isinstance(window_minutes, bool)
        or not isinstance(window_minutes, int)
        or not 1 <= window_minutes <= 1440
    ):
        raise ValueError("window_minutes must be between 1 and 1440")

    end_time = datetime.fromisoformat(around.replace("Z", "+00:00"))
    start_time = end_time - timedelta(minutes=window_minutes)

    matching_ids = []

    with ALERTS_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            alert = json.loads(line)

            alert_rule = str(alert["rule"]["id"])
            alert_agent = alert["agent"]["name"]

            if alert_rule != str(rule_id):
                continue

            if alert_agent.casefold() != agent.casefold():
                continue

            alert_time = datetime.fromisoformat(
                alert["timestamp"].replace("Z", "+00:00")
            )

            if start_time <= alert_time <= end_time:
                matching_ids.append(alert["id"])

    return {
        "count": len(matching_ids),
        "alert_ids": matching_ids,
    }


# Python functions used by the triage agent.
TOOLS: dict = {
    "lookup_asset": lookup_asset,
    "search_runbooks": search_runbooks,
    "related_alerts": related_alerts,
}


# JSON schemas shared with the MCP server and triage agent.
TOOL_SCHEMAS: list = [
    {
        "name": "lookup_asset",
        "description": "Look up asset ownership, criticality and environment using its hostname.",
        "input_schema": {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
            },
            "required": ["host"],
            "additionalProperties": False,
        },
    },
    {
        "name": "search_runbooks",
        "description": "Search Hisn SOC runbooks and return the most relevant procedures.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "k": {"type": "integer"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "related_alerts",
        "description": "Count alerts with the same rule and agent within a time window.",
        "input_schema": {
            "type": "object",
            "properties": {
                "rule_id": {"type": "string"},
                "agent": {"type": "string"},
                "around": {"type": "string"},
                "window_minutes": {"type": "integer"},
            },
            "required": ["rule_id", "agent", "around"],
            "additionalProperties": False,
        },
    },
]
