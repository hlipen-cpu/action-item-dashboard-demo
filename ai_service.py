"""Replaceable adapter for the approved on-premises AI API.

The API contract is intentionally configurable because the final endpoint and
authentication method have not yet been supplied. The deterministic fallback
keeps the dashboard usable when the API is unavailable.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

import pandas as pd

from action_dashboard_core import key_points, potential_links, reminder_draft


def _api_url() -> str:
    return os.getenv("ONPREM_AI_URL", "").strip()


def _call_api(payload: dict[str, Any]) -> dict[str, Any] | None:
    url = _api_url()
    if not url:
        return None
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return None


def generate_follow_up(row: pd.Series) -> dict[str, Any]:
    payload = {
        "task": "draft_follow_up",
        "action": {key: (None if pd.isna(value) else str(value)) for key, value in row.items()},
    }
    result = _call_api(payload)
    if result:
        return {
            "reminder": result.get("reminder", reminder_draft(row)),
            "key_points": result.get("key_points", key_points(row)),
            "source": "On-prem AI API",
        }
    return {
        "reminder": reminder_draft(row),
        "key_points": key_points(row),
        "source": "Deterministic fallback — on-prem AI API not connected",
    }


def generate_link_suggestions(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    payload = {
        "task": "suggest_historical_links",
        "actions": df.to_dict(orient="records"),
    }
    result = _call_api(payload)
    if result and isinstance(result.get("links"), list):
        return pd.DataFrame(result["links"]), "On-prem AI API"
    return potential_links(df), "Deterministic fallback — on-prem AI API not connected"

