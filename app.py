"""Streamlit prototype for the Action Item Management and Tracking System."""

from __future__ import annotations

import io
import os
import shutil
from datetime import date, datetime
from pathlib import Path

import pandas as pd

try:
    import streamlit as st
except ImportError as exc:  # pragma: no cover - clear message when not installed
    raise SystemExit("Streamlit is required. Install dependencies from requirements.txt.") from exc

from action_dashboard_core import (
    REQUIRED_COLUMNS,
    STATUS_VALUES,
    add_deadline_fields,
    compare_registers,
    dashboard_metrics,
    dependency_summary,
    normalize_register,
)
from ai_service import generate_follow_up, generate_link_suggestions


APP_DIR = Path(__file__).resolve().parent
DEFAULT_DEMO_FILE = APP_DIR / "action_register_demo.xlsx"
WORKING_FILE = Path(os.getenv("ACTION_REGISTER_FILE", APP_DIR / "action_register_working.xlsx"))
ARCHIVE_DIR = Path(os.getenv("ACTION_REGISTER_ARCHIVE_DIR", APP_DIR / "archive"))


def load_workbook(path_or_buffer) -> tuple[pd.DataFrame, pd.DataFrame]:
    actions = pd.read_excel(path_or_buffer, sheet_name="Action Register")
    try:
        audit = pd.read_excel(path_or_buffer, sheet_name="Audit Log")
    except (ValueError, KeyError):
        audit = pd.DataFrame(columns=["Timestamp", "User", "Action ID", "Field", "Previous value", "New value"])
    return normalize_register(actions), audit


def export_workbook(actions: pd.DataFrame, audit: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl", date_format="yyyy-mm-dd", datetime_format="yyyy-mm-dd hh:mm") as writer:
        actions.to_excel(writer, sheet_name="Action Register", index=False)
        audit.to_excel(writer, sheet_name="Audit Log", index=False)
        pd.DataFrame(
            {
                "Field": ["Purpose", "Deadline logic", "AI boundary"],
                "Definition": [
                    "Editable source register for one project demonstration.",
                    "15–21 days Reminder; 8–14 days Action needed; 0–7 days Critical; passed due date Overdue.",
                    "On-prem API adapter only. No automatic sending. Human review required.",
                ],
            }
        ).to_excel(writer, sheet_name="Read Me", index=False)
    return output.getvalue()


def archive_and_save(actions: pd.DataFrame, audit: pd.DataFrame, user: str) -> Path:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    if WORKING_FILE.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(WORKING_FILE, ARCHIVE_DIR / f"{WORKING_FILE.stem}_{stamp}{WORKING_FILE.suffix}")
    WORKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    WORKING_FILE.write_bytes(export_workbook(actions, audit))
    return WORKING_FILE


def ensure_state() -> None:
    if "actions" in st.session_state:
        return
    source = WORKING_FILE if WORKING_FILE.exists() else DEFAULT_DEMO_FILE
    st.session_state.actions, st.session_state.audit = load_workbook(source)
    st.session_state.source_name = source.name
    st.session_state.original_actions = st.session_state.actions.copy(deep=True)


st.set_page_config(page_title="Action Item Management Dashboard", page_icon="✓", layout="wide")
ensure_state()

st.title("Action Item Management and Tracking System")
st.caption("Single-project demonstration • Excel source of truth • Human-reviewed follow-up")
st.warning("Demonstration data only. Do not enter classified information in this session. The classified deployment requires the approved on-premises environment and AI API.")

with st.sidebar:
    st.header("Controls")
    as_of = st.date_input("As-of date", value=date.today())
    user = st.text_input("Update user", value="")
    uploaded = st.file_uploader("Load Excel action register", type=["xlsx"])
    if uploaded is not None and st.button("Load uploaded register"):
        st.session_state.actions, st.session_state.audit = load_workbook(uploaded)
        st.session_state.source_name = uploaded.name
        st.session_state.original_actions = st.session_state.actions.copy(deep=True)
        st.rerun()
    st.divider()
    st.write("AI connection")
    if os.getenv("ONPREM_AI_URL"):
        st.success("On-prem AI API configured")
    else:
        st.info("On-prem AI API not configured; deterministic fallback is active")

actions = add_deadline_fields(st.session_state.actions, as_of)
metrics = dashboard_metrics(actions)

cards = st.columns(7)
labels = [
    ("Total", metrics["total"]),
    ("Outstanding", metrics["outstanding"]),
    ("Overdue", metrics["overdue"]),
    ("Reminder", metrics["reminder"]),
    ("Action needed", metrics["action_needed"]),
    ("Critical", metrics["critical"]),
    ("Blocked", metrics["blocked"]),
]
for card, (label, value) in zip(cards, labels):
    card.metric(label, value)

tab_overview, tab_register, tab_links, tab_followup, tab_audit = st.tabs(
    ["Overview", "Action register", "Dependencies and history", "Follow-up drafts", "Audit and archive"]
)

with tab_overview:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Deadline overview")
        deadline_counts = (
            actions["Deadline band"]
            .value_counts()
            .reindex(["Overdue", "Critical", "Action needed", "Reminder", "On track", "Missing due date"], fill_value=0)
            .rename_axis("Deadline band")
            .reset_index(name="Count")
        )
        st.dataframe(deadline_counts, hide_index=True, use_container_width=True)
    with right:
        st.subheader("Actions requiring attention")
        attention = actions[
            actions["Deadline band"].isin(["Overdue", "Critical", "Action needed"])
            | actions["Status"].isin(["Blocked"])
        ][["Action ID", "Action description", "Owner", "Status", "Due date", "Deadline band"]]
        st.dataframe(attention, hide_index=True, use_container_width=True)

with tab_register:
    st.subheader("Editable action register")
    st.caption("Edit permitted fields, then save. A prior workbook version is archived before overwrite.")
    editable = actions.copy()
    edited = st.data_editor(
        editable,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "Due date": st.column_config.DateColumn("Due date", format="YYYY-MM-DD"),
            "Last updated date": st.column_config.DateColumn("Last updated date", format="YYYY-MM-DD"),
            "Status": st.column_config.SelectboxColumn("Status", options=STATUS_VALUES),
            "Days remaining": st.column_config.NumberColumn("Days remaining", disabled=True),
            "Deadline band": st.column_config.TextColumn("Deadline band", disabled=True),
        },
        disabled=["Days remaining", "Deadline band"],
        key="action_editor",
    )
    if st.button("Save changes to working Excel file", type="primary"):
        if not user.strip():
            st.error("Enter the update user before saving for traceability.")
        else:
            updated = normalize_register(edited)
            changes = compare_registers(st.session_state.original_actions, updated)
            if not changes:
                st.info("No changes detected.")
            else:
                updated["Last updated by"] = user.strip()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                audit_rows = st.session_state.audit.copy()
                new_audit = pd.DataFrame(
                    [
                        {"Timestamp": timestamp, "User": user.strip(), **change}
                        for change in changes
                    ]
                )
                audit_rows = pd.concat([audit_rows, new_audit], ignore_index=True)
                archive_and_save(updated, audit_rows, user.strip())
                st.session_state.actions = updated
                st.session_state.audit = audit_rows
                st.session_state.original_actions = updated.copy(deep=True)
                st.success(f"Saved {len(changes)} field change(s). Previous version archived.")

with tab_links:
    st.subheader("Dependencies and historical linkages")
    deps = dependency_summary(actions)
    if deps.empty:
        st.info("No explicit dependencies are recorded.")
    else:
        st.write("Confirmed dependencies from the Excel register")
        st.dataframe(deps, hide_index=True, use_container_width=True)
    links, source = generate_link_suggestions(actions)
    st.write(f"Potential historical links ({source})")
    if links.empty:
        st.info("No potential links identified by the current method.")
    else:
        st.dataframe(links, hide_index=True, use_container_width=True)

with tab_followup:
    st.subheader("Draft reminders and key points")
    candidates = actions[
        actions["Deadline band"].isin(["Overdue", "Critical", "Action needed"])
        | actions["Status"].isin(["Blocked"])
    ]
    if candidates.empty:
        st.info("No immediate follow-up candidates.")
    else:
        selected_id = st.selectbox("Select an action", candidates["Action ID"].tolist())
        selected = candidates[candidates["Action ID"] == selected_id].iloc[0]
        result = generate_follow_up(selected)
        st.caption(result["source"])
        st.text_area("Draft reminder", result["reminder"], height=180)
        st.write("Key points to note")
        for point in result["key_points"]:
            st.write(f"- {point}")
        st.info("Draft only. Nothing is sent automatically.")

with tab_audit:
    st.subheader("Audit trail and archived versions")
    if st.session_state.audit.empty:
        st.info("No updates have been made in this session.")
    else:
        st.dataframe(st.session_state.audit, hide_index=True, use_container_width=True)
    archive_files = sorted(ARCHIVE_DIR.glob("*.xlsx")) if ARCHIVE_DIR.exists() else []
    st.write(f"Archived workbook versions: {len(archive_files)}")
    if archive_files:
        st.code("\n".join(file.name for file in archive_files[-10:]))

st.divider()
st.download_button(
    "Download current workbook",
    data=export_workbook(actions, st.session_state.audit),
    file_name="action_register_current.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
