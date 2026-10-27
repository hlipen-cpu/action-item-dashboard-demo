# Action Item Management and Tracking System

This is a practical-option prototype for a single-project action dashboard.
It uses an editable Excel workbook as the source of truth and includes selected
creative features for dependency visibility and historical-action linkage.

## Demonstration scope

- Synthetic, de-identified demonstration data only.
- Deadline bands for open actions: 15–21 days = Reminder; 8–14 days = Action needed; 0–7 days = Critical; passed due date = Overdue. Completed and cancelled actions are excluded from overdue counts.
- Users can edit the register, save changes, archive the previous working workbook and download the current workbook.
- Every saved change records the update user and field-level previous/new values.
- Follow-up messages are drafts only. The prototype does not send messages.
- Potential historical links are labelled as suggestions and require review.

## Run locally

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
streamlit run app.py
```

The demo workbook is `action_register_demo.xlsx`. To use a different working
file, set `ACTION_REGISTER_FILE`. To use a separate archive directory, set
`ACTION_REGISTER_ARCHIVE_DIR`.

## On-premises AI API adapter

Set `ONPREM_AI_URL` to the approved internal API endpoint. The adapter sends a
JSON request with `task` and `action` or `actions` fields. The expected response
shape is currently a placeholder because the final API contract has not been
provided:

```json
{
  "reminder": "...",
  "key_points": ["..."],
  "links": []
}
```

Authentication, endpoint, model identifier, network controls and API contract
must be completed in the approved classified environment. The dashboard uses
a deterministic fallback when the API is not configured.

## Important limitation

This development session is not an approved classified environment. Do not
enter classified information here. The prototype is structured so its core
Excel tracking functions can run locally, with the AI adapter enabled only in
the approved on-premises deployment.
