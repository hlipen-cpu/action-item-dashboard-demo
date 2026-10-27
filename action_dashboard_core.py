"""Core, deterministic action-register logic for the prototype dashboard."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = [
    "Action ID",
    "Project",
    "Action description",
    "Owner",
    "Status",
    "Due date",
    "Dependency or predecessor action",
    "Related past action",
    "Source meeting or discussion",
    "Notes",
    "Last updated date",
    "Discussion outcome",
    "Agreed next step",
]

SYSTEM_COLUMNS = ["Days remaining", "Deadline band", "Last updated by"]

STATUS_VALUES = ["Not Started", "In Progress", "Blocked", "Completed", "Cancelled"]


def normalize_register(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with required columns present and dates normalized."""
    result = df.copy()
    for column in REQUIRED_COLUMNS + SYSTEM_COLUMNS:
        if column not in result.columns:
            result[column] = ""
    result["Due date"] = pd.to_datetime(result["Due date"], errors="coerce")
    result["Last updated date"] = pd.to_datetime(
        result["Last updated date"], errors="coerce"
    )
    for column in [
        "Action ID",
        "Project",
        "Action description",
        "Owner",
        "Status",
        "Dependency or predecessor action",
        "Related past action",
        "Source meeting or discussion",
        "Notes",
        "Last updated by",
    ]:
        result[column] = result[column].fillna("").astype(str)
    return result


def classify_deadline(due_date: Any, as_of: date) -> tuple[Any, str]:
    """Return (days remaining, deadline band) using calendar days."""
    if pd.isna(due_date) or due_date in ("", None):
        return pd.NA, "Missing due date"
    due = pd.Timestamp(due_date).date()
    days = (due - as_of).days
    if days < 0:
        return days, "Overdue"
    if days <= 7:
        return days, "Critical"
    if days <= 14:
        return days, "Action needed"
    if days <= 21:
        return days, "Reminder"
    return days, "On track"


def add_deadline_fields(df: pd.DataFrame, as_of: date) -> pd.DataFrame:
    result = normalize_register(df)
    values = []
    for _, row in result.iterrows():
        days, band = classify_deadline(row["Due date"], as_of)
        if row["Status"] == "Completed":
            band = "Completed"
        elif row["Status"] == "Cancelled":
            band = "Cancelled"
        values.append((days, band))
    result["Days remaining"] = [value[0] for value in values]
    result["Deadline band"] = [value[1] for value in values]
    return result


def dashboard_metrics(df: pd.DataFrame) -> dict[str, int]:
    result = normalize_register(df)
    return {
        "total": len(result),
        "outstanding": int((~result["Status"].isin(["Completed", "Cancelled"])).sum()),
        "overdue": int((result["Deadline band"] == "Overdue").sum()),
        "reminder": int((result["Deadline band"] == "Reminder").sum()),
        "action_needed": int((result["Deadline band"] == "Action needed").sum()),
        "critical": int((result["Deadline band"] == "Critical").sum()),
        "blocked": int((result["Status"] == "Blocked").sum()),
    }


def split_ids(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [item.strip() for item in str(value).replace(";", ",").split(",") if item.strip()]


def dependency_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return a compact list of actions with explicit dependencies."""
    result = add_deadline_fields(df, date.today())
    rows = []
    for _, row in result.iterrows():
        dependencies = split_ids(row["Dependency or predecessor action"])
        if dependencies:
            rows.append(
                {
                    "Action ID": row["Action ID"],
                    "Action": row["Action description"],
                    "Depends on": ", ".join(dependencies),
                    "Status": row["Status"],
                    "Deadline band": row["Deadline band"],
                }
            )
    return pd.DataFrame(rows)


def _tokens(text: Any) -> set[str]:
    words = {word.lower().strip(".,:;()[]") for word in str(text).split()}
    return {word for word in words if len(word) >= 5}


def potential_links(df: pd.DataFrame) -> pd.DataFrame:
    """Create transparent, deterministic linkage suggestions for the demo.

    This is a fallback for when the on-prem AI API is not connected. It is not
    presented as a confirmed relationship.
    """
    result = normalize_register(df)
    rows = []
    for index, row in result.iterrows():
        current_tokens = _tokens(row["Action description"])
        if not current_tokens:
            continue
        for other_index, other in result.iterrows():
            if index == other_index:
                continue
            if other["Status"] not in ["Completed", "Cancelled"]:
                continue
            overlap = current_tokens & _tokens(other["Action description"])
            if len(overlap) >= 2:
                rows.append(
                    {
                        "Action ID": row["Action ID"],
                        "Potential past action": other["Action ID"],
                        "Shared terms": ", ".join(sorted(overlap)),
                        "Review status": "Potential link — review required",
                    }
                )
                break
    return pd.DataFrame(rows)


def reminder_draft(row: pd.Series) -> str:
    owner = row.get("Owner", "MISSING") or "MISSING"
    due = row.get("Due date", "MISSING")
    due_text = pd.Timestamp(due).strftime("%Y-%m-%d") if not pd.isna(due) else "MISSING"
    action = row.get("Action description", "MISSING") or "MISSING"
    band = row.get("Deadline band", "MISSING")
    return (
        f"Follow-up on {row.get('Action ID', 'MISSING')}: {action}\n\n"
        f"Owner: {owner}\nDue date: {due_text}\nDeadline indicator: {band}\n\n"
        "Please provide the current progress, any blocker or dependency, and the next expected step."
    )


def key_points(row: pd.Series) -> list[str]:
    points = [f"Action: {row.get('Action ID', 'MISSING')} — {row.get('Action description', 'MISSING')}"]
    points.append(f"Owner: {row.get('Owner', '') or 'MISSING'}")
    points.append(f"Deadline: {row.get('Deadline band', 'MISSING')}")
    if row.get("Dependency or predecessor action"):
        points.append(f"Dependency: {row['Dependency or predecessor action']}")
    if row.get("Notes"):
        points.append(f"Latest note: {row['Notes']}")
    return points


def compare_registers(before: pd.DataFrame, after: pd.DataFrame) -> list[dict[str, Any]]:
    """Return field-level changes keyed by Action ID."""
    before_n = normalize_register(before).set_index("Action ID", drop=False)
    after_n = normalize_register(after).set_index("Action ID", drop=False)
    changes: list[dict[str, Any]] = []
    common_ids = sorted(set(before_n.index) & set(after_n.index))
    tracked = REQUIRED_COLUMNS[1:] + ["Last updated by"]
    for action_id in common_ids:
        for field in tracked:
            old = before_n.loc[action_id, field]
            new = after_n.loc[action_id, field]
            old_text = "" if pd.isna(old) else str(old)
            new_text = "" if pd.isna(new) else str(new)
            if old_text != new_text:
                changes.append(
                    {
                        "Action ID": action_id,
                        "Field": field,
                        "Previous value": old_text,
                        "New value": new_text,
                    }
                )
    return changes

