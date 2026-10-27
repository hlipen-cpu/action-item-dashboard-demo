"""Discussion-focused action-item follow-up dashboard."""
from __future__ import annotations

import io
import os
import shutil
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from action_dashboard_core import STATUS_VALUES, add_deadline_fields, compare_registers, dashboard_metrics, dependency_summary, normalize_register
from ai_service import generate_link_suggestions

APP_DIR = Path(__file__).resolve().parent
DEFAULT_DEMO_FILE = APP_DIR / "action_register_demo.xlsx"
WORKING_FILE = Path(os.getenv("ACTION_REGISTER_FILE", APP_DIR / "action_register_working.xlsx"))
ARCHIVE_DIR = Path(os.getenv("ACTION_REGISTER_ARCHIVE_DIR", APP_DIR / "archive"))
AUDIT_COLUMNS = ["Timestamp", "User", "Action ID", "Field", "Previous value", "New value"]
BANDS = ["Overdue", "Critical", "Action needed", "Reminder", "On track", "Missing due date"]
DISCUSSION_BANDS = ["Overdue", "Critical", "Blocked", "Action needed", "Reminder"]
COLOURS = {"Overdue": ("#7f1d1d", "#fee2e2"), "Critical": ("#c2410c", "#ffedd5"), "Action needed": ("#a16207", "#fef9c3"), "Reminder": ("#854d0e", "#fefce8"), "On track": ("#166534", "#dcfce7"), "Blocked": ("#6b21a8", "#f3e8ff"), "Missing due date": ("#374151", "#f3f4f6"), "Completed": ("#1d4ed8", "#dbeafe"), "Cancelled": ("#4b5563", "#e5e7eb")}

def load_workbook(source):
    actions = pd.read_excel(source, sheet_name="Action Register")
    try:
        audit = pd.read_excel(source, sheet_name="Audit Log")
    except (ValueError, KeyError):
        audit = pd.DataFrame(columns=AUDIT_COLUMNS)
    return normalize_register(actions), audit

def export_workbook(actions: pd.DataFrame, audit: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl", date_format="yyyy-mm-dd", datetime_format="yyyy-mm-dd hh:mm") as writer:
        actions.to_excel(writer, sheet_name="Action Register", index=False)
        audit.to_excel(writer, sheet_name="Audit Log", index=False)
        pd.DataFrame({"Field": ["Deadline logic", "Outstanding", "Overdue", "Blocked", "AI boundary"], "Definition": ["15–21 days Reminder; 8–14 days Action needed; 0–7 days Critical; passed due date Overdue.", "Open actions not marked Completed or Cancelled.", "Outstanding action whose due date has passed.", "Action unable to progress because a dependency, decision, resource, access, or approval is unavailable.", "On-prem API adapter only; human review required."]}).to_excel(writer, sheet_name="Read Me", index=False)
    return output.getvalue()

def archive_and_save(actions, audit):
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    if WORKING_FILE.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(WORKING_FILE, ARCHIVE_DIR / f"{WORKING_FILE.stem}_{stamp}{WORKING_FILE.suffix}")
    WORKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    WORKING_FILE.write_bytes(export_workbook(actions, audit))

def ensure_state():
    if "actions" not in st.session_state:
        source = WORKING_FILE if WORKING_FILE.exists() else DEFAULT_DEMO_FILE
        st.session_state.actions, st.session_state.audit = load_workbook(source)
        st.session_state.source_name = source.name
        st.session_state.original_actions = st.session_state.actions.copy(deep=True)
    st.session_state.setdefault("selected_action_id", None)

def save_changes(updated, user):
    if not user.strip():
        st.error("Enter the update user before saving for traceability.")
        return False
    updated = normalize_register(updated)
    changes = compare_registers(st.session_state.original_actions, updated)
    if not changes:
        st.info("No changes detected.")
        return False
    updated["Last updated by"] = user.strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    audit = pd.concat([st.session_state.audit, pd.DataFrame([{"Timestamp": timestamp, "User": user.strip(), **c} for c in changes])], ignore_index=True)
    archive_and_save(updated, audit)
    st.session_state.actions, st.session_state.audit = updated, audit
    st.session_state.original_actions = updated.copy(deep=True)
    st.success(f"Saved {len(changes)} field change(s). Previous version archived.")
    return True

def styled_band(value):
    fg, bg = COLOURS.get(value, ("#111827", "#ffffff"))
    return f"background-color: {bg}; color: {fg}; font-weight: 700"

st.set_page_config(page_title="Action Item Follow-up Dashboard", page_icon="✓", layout="wide")
ensure_state()
st.markdown("<style>.metric-card{padding:10px;border-radius:8px;border:1px solid #d1d5db}.definition{background:#f8fafc;border-left:4px solid #2563eb;padding:10px 14px;border-radius:4px}</style>", unsafe_allow_html=True)
st.title("Action Item Follow-up Dashboard")
st.caption("Single-project discussion view • Excel source of truth • Human-reviewed updates")
st.warning("Demonstration data only. Do not enter classified information in this session. Use the approved on-premises environment for classified deployment.")

with st.sidebar:
    st.header("Controls")
    as_of = st.date_input("As-of date", value=date.today())
    user = st.text_input("Update user", value="")
    uploaded = st.file_uploader("Load Excel action register", type=["xlsx"])
    if uploaded is not None and st.button("Load uploaded register"):
        st.session_state.actions, st.session_state.audit = load_workbook(uploaded)
        st.session_state.source_name = uploaded.name
        st.session_state.original_actions = st.session_state.actions.copy(deep=True)
        st.session_state.selected_action_id = None
        st.rerun()
    st.divider()
    st.write("AI connection")
    st.success("On-prem AI API configured") if os.getenv("ONPREM_AI_URL") else st.info("On-prem AI API not configured; deterministic fallback is active")

actions = add_deadline_fields(st.session_state.actions, as_of)
metrics = dashboard_metrics(actions)
open_actions = actions[~actions["Status"].isin(["Completed", "Cancelled"])].copy()

st.subheader("Situation overview")
specs = [("Total", metrics["total"], None), ("Outstanding", metrics["outstanding"], "All open actions"), ("Overdue", metrics["overdue"], "Overdue"), ("Critical", metrics["critical"], "Critical"), ("Action needed", metrics["action_needed"], "Action needed"), ("Blocked", metrics["blocked"], "Blocked"), ("Reminder", metrics["reminder"], "Reminder")]
cards = st.columns(len(specs))
for col, (label, value, selection) in zip(cards, specs):
    if selection and col.button(f"{label}: {value}", key=f"card_{label}", use_container_width=True):
        st.session_state.selected_category = selection
        st.session_state.selected_action_id = None
    col.caption(label if selection is None else "Click to filter discussion")
st.markdown("<div class='definition'><b>Outstanding</b> means open and not Completed or Cancelled. <b>Overdue</b> is a subset of outstanding actions whose due date has passed. <b>Blocked</b> means progress cannot continue because a dependency, decision, resource, access, or approval is unavailable.</div>", unsafe_allow_html=True)

tab_overview, tab_discussion, tab_register, tab_links, tab_audit = st.tabs(["Overview", "Follow-up discussion", "Action register", "Dependencies and history", "Audit and archive"])
with tab_overview:
    st.subheader("Actions requiring attention")
    left, right = st.columns([1, 2])
    counts = actions["Deadline band"].value_counts().reindex(BANDS + ["Completed", "Cancelled"], fill_value=0).rename_axis("Category").reset_index(name="Count")
    left.dataframe(counts.style.map(lambda v: styled_band(v) if v in COLOURS else "", subset=["Category"]), hide_index=True, use_container_width=True)
    attention = actions[(actions["Deadline band"].isin(DISCUSSION_BANDS)) & (~actions["Status"].isin(["Completed", "Cancelled"]))].copy()
    attention["_order"] = attention["Deadline band"].map({"Overdue": 0, "Critical": 1, "Blocked": 2, "Action needed": 3, "Reminder": 4}).fillna(9)
    attention = attention.sort_values(["_order", "Days remaining"], na_position="last").drop(columns=["_order"])
    cols = ["Action ID", "Action description", "Owner", "Status", "Due date", "Days remaining", "Deadline band"]
    right.dataframe(attention[cols].style.map(lambda v: styled_band(v) if v in COLOURS else "", subset=["Deadline band"]), hide_index=True, use_container_width=True)
    right.download_button("Download follow-up list", data=export_workbook(attention, pd.DataFrame(columns=AUDIT_COLUMNS)), file_name="action_follow_up_list.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tab_discussion:
    st.subheader("Follow-up discussion")
    st.caption("Select a concern category, choose an action, discuss it, and record the outcome and agreed next step.")
    c1, c2, c3 = st.columns(3)
    category_options = ["All open actions"] + DISCUSSION_BANDS
    category = c1.selectbox("Concern category", category_options, index=category_options.index(st.session_state.get("selected_category", "All open actions")) if st.session_state.get("selected_category", "All open actions") in category_options else 0)
    owner = c2.selectbox("Owner", ["All owners"] + sorted([x for x in open_actions["Owner"].unique() if x]))
    status = c3.selectbox("Status", ["All open statuses"] + [x for x in STATUS_VALUES if x not in ["Completed", "Cancelled"]])
    discussion = open_actions.copy()
    if category != "All open actions": discussion = discussion[(discussion["Deadline band"] == category) | ((category == "Blocked") & (discussion["Status"] == "Blocked"))]
    if owner != "All owners": discussion = discussion[discussion["Owner"] == owner]
    if status != "All open statuses": discussion = discussion[discussion["Status"] == status]
    discussion["_order"] = discussion["Deadline band"].map({"Overdue": 0, "Critical": 1, "Blocked": 2, "Action needed": 3, "Reminder": 4, "On track": 5}).fillna(9)
    discussion = discussion.sort_values(["_order", "Days remaining"], na_position="last").drop(columns=["_order"])
    if discussion.empty:
        st.info("No actions match the selected filters.")
    else:
        ids = discussion["Action ID"].tolist()
        current = st.session_state.selected_action_id if st.session_state.selected_action_id in ids else ids[0]
        selected_id = st.selectbox("Action for discussion", ids, index=ids.index(current), format_func=lambda x: f"{x} — {discussion.loc[discussion['Action ID'] == x, 'Action description'].iloc[0]}")
        st.session_state.selected_action_id = selected_id
        row = discussion[discussion["Action ID"] == selected_id].iloc[0]
        fg, bg = COLOURS.get(row["Deadline band"], ("#111827", "#fff"))
        st.markdown(f"<div style='padding:12px;border-radius:8px;background:{bg};color:{fg};font-weight:700'>{row['Deadline band']} · {row['Status']} · {row['Days remaining'] if pd.notna(row['Days remaining']) else '—'} days remaining</div>", unsafe_allow_html=True)
        st.write(f"**{row['Action ID']} — {row['Action description']}**")
        details = pd.DataFrame([{"Owner": row["Owner"] or "Missing", "Due date": row["Due date"], "Dependency": row["Dependency or predecessor action"] or "None recorded", "Source": row["Source meeting or discussion"] or "Not recorded", "Related past action": row["Related past action"] or "None recorded", "Latest notes": row["Notes"] or "No notes recorded"}])
        st.dataframe(details, hide_index=True, use_container_width=True)
        with st.form(f"discussion_form_{selected_id}"):
            new_status = st.selectbox("Status", STATUS_VALUES, index=STATUS_VALUES.index(row["Status"]) if row["Status"] in STATUS_VALUES else 0)
            outcome = st.text_area("Discussion outcome", value=row["Discussion outcome"], placeholder="Record the decision, progress update, or reason for no change.")
            next_step = st.text_area("Agreed next step", value=row["Agreed next step"], placeholder="Record the next concrete action and expected result.")
            notes = st.text_area("Progress remarks / blocker explanation", value=row["Notes"], placeholder="Required when status is Blocked.")
            due = st.date_input("Updated due date", value=row["Due date"].date() if pd.notna(row["Due date"]) else None)
            submitted = st.form_submit_button("Save discussion update", type="primary")
        if submitted:
            if new_status == "Blocked" and not notes.strip(): st.error("A blocker explanation is required when status is Blocked.")
            elif new_status not in ["Completed", "Cancelled"] and not next_step.strip(): st.error("Enter an agreed next step for an open action.")
            else:
                updated = st.session_state.actions.copy()
                idx = updated.index[updated["Action ID"] == selected_id][0]
                updated.loc[idx, ["Status", "Discussion outcome", "Agreed next step", "Notes", "Due date", "Last updated date"]] = [new_status, outcome, next_step, notes, pd.Timestamp(due) if due else pd.NaT, pd.Timestamp.today()]
                save_changes(updated, user)

with tab_register:
    st.subheader("Editable action register")
    st.caption("Use this for broad register edits. Use Follow-up discussion for meeting updates.")
    edited = st.data_editor(actions, hide_index=True, use_container_width=True, num_rows="fixed", column_config={"Due date": st.column_config.DateColumn("Due date", format="YYYY-MM-DD"), "Last updated date": st.column_config.DateColumn("Last updated date", format="YYYY-MM-DD"), "Status": st.column_config.SelectboxColumn("Status", options=STATUS_VALUES), "Days remaining": st.column_config.NumberColumn("Days remaining", disabled=True), "Deadline band": st.column_config.TextColumn("Deadline band", disabled=True)}, disabled=["Days remaining", "Deadline band"], key="action_editor")
    if st.button("Save register changes", type="primary"):
        invalid = edited[(edited["Status"] == "Blocked") & (edited["Notes"].fillna("").astype(str).str.strip() == "")]
        st.error("Blocked actions require a blocker explanation in Notes.") if not invalid.empty else save_changes(edited, user)

with tab_links:
    st.subheader("Dependencies and historical linkages")
    deps = dependency_summary(actions)
    st.dataframe(deps, hide_index=True, use_container_width=True) if not deps.empty else st.info("No explicit dependencies are recorded.")
    links, source = generate_link_suggestions(actions)
    st.write(f"Potential historical links ({source})")
    st.dataframe(links, hide_index=True, use_container_width=True) if not links.empty else st.info("No potential links identified.")

with tab_audit:
    st.subheader("Audit trail and archived versions")
    st.dataframe(st.session_state.audit, hide_index=True, use_container_width=True) if not st.session_state.audit.empty else st.info("No updates have been made.")
    archive_files = sorted(ARCHIVE_DIR.glob("*.xlsx")) if ARCHIVE_DIR.exists() else []
    st.write(f"Archived workbook versions: {len(archive_files)}")
    if archive_files: st.code("\n".join(file.name for file in archive_files[-10:]))

st.divider()
st.download_button("Download current workbook", data=export_workbook(actions, st.session_state.audit), file_name="action_register_current.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
