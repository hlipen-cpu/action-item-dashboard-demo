import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "/workspace/scratch/ac88202a8b2d/action_dashboard_build/output";
const d = (year, month, day) => new Date(year, month - 1, day);

const headers = [
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
  "Last updated by",
  "Days remaining",
  "Deadline band",
];

const project = "Synthetic Aircraft Systems Demonstration";
const rows = [
  ["A-001", project, "Confirm the draft systems integration baseline", "Systems Lead", "In Progress", d(2026, 11, 17), "", "A-017", "Systems Integration Review — 01 Oct 2026", "Baseline comments are being consolidated.", d(2026, 10, 27), "Demo User"],
  ["A-002", project, "Resolve avionics interface control document comments", "Avionics Lead", "In Progress", d(2026, 11, 10), "A-001", "A-018", "Systems Integration Review — 01 Oct 2026", "Waiting for consolidated interface comments.", d(2026, 10, 27), "Demo User"],
  ["A-003", project, "Confirm test equipment availability for interface checks", "Test Manager", "Blocked", d(2026, 11, 3), "A-002", "A-019", "Systems Integration Review — 01 Oct 2026", "Blocked until the interface baseline is confirmed.", d(2026, 10, 27), "Demo User"],
  ["A-004", project, "Update the ground-support equipment interface checklist", "Ground Systems Lead", "Not Started", d(2026, 11, 24), "A-001", "A-020", "Ground Systems Progress Review — 08 Oct 2026", "Checklist structure requires review.", d(2026, 10, 27), "Demo User"],
  ["A-005", project, "Confirm power and cooling assumptions for the test configuration", "Facilities Lead", "In Progress", d(2026, 12, 8), "", "A-021", "Ground Systems Progress Review — 08 Oct 2026", "Assumptions are being checked against the latest configuration.", d(2026, 10, 27), "Demo User"],
  ["A-006", project, "Prepare an updated risk note for the integration schedule", "Project Manager", "In Progress", d(2026, 11, 20), "A-002", "A-022", "Ground Systems Progress Review — 08 Oct 2026", "Risk note will include the interface closure dependency.", d(2026, 10, 27), "Demo User"],
  ["A-007", project, "Confirm the data package required for the readiness review", "Configuration Lead", "Not Started", d(2026, 12, 1), "", "A-023", "Ground Systems Progress Review — 08 Oct 2026", "Package contents are being drafted.", d(2026, 10, 27), "Demo User"],
  ["A-008", project, "Review the open ground-test discrepancies", "Verification Lead", "Blocked", d(2026, 10, 25), "A-003", "A-024", "Ground Systems Progress Review — 08 Oct 2026", "Review depends on the interface test equipment decision.", d(2026, 10, 27), "Demo User"],
  ["A-009", project, "Issue the draft flight-test readiness agenda", "Test Manager", "In Progress", d(2026, 11, 14), "A-007", "A-017", "Flight Test Readiness Review — 15 Oct 2026", "Agenda is being coordinated with workstream leads.", d(2026, 10, 27), "Demo User"],
  ["A-010", project, "Confirm the latest configuration status for readiness review", "Configuration Lead", "In Progress", d(2026, 11, 12), "A-007", "A-018", "Flight Test Readiness Review — 15 Oct 2026", "Current configuration list requires final owner confirmation.", d(2026, 10, 27), "Demo User"],
  ["A-011", project, "Prepare a dependency map for unresolved test actions", "Project Manager", "Not Started", d(2026, 12, 15), "A-008", "A-019", "Flight Test Readiness Review — 15 Oct 2026", "Map will link open test actions to decisions.", d(2026, 10, 27), "Demo User"],
  ["A-012", project, "Confirm review attendees and decision owners", "Project Manager", "Completed", d(2026, 10, 24), "", "A-020", "Flight Test Readiness Review — 15 Oct 2026", "Completed; attendance list issued.", d(2026, 10, 27), "Demo User"],
  ["A-013", project, "Update the integration schedule with confirmed test gates", "Planning Lead", "In Progress", d(2026, 11, 28), "A-001, A-002", "A-021", "Flight Test Readiness Review — 15 Oct 2026", "Schedule update follows interface baseline closure.", d(2026, 10, 27), "Demo User"],
  ["A-014", project, "Review the draft operational support checklist", "Operations Lead", "Not Started", d(2026, 12, 5), "A-004", "A-022", "Flight Test Readiness Review — 15 Oct 2026", "Checklist will use the updated ground interface assumptions.", d(2026, 10, 27), "Demo User"],
  ["A-015", project, "Prepare a summary of decisions requiring senior review", "Project Manager", "In Progress", d(2026, 10, 26), "A-003, A-008", "A-023", "Flight Test Readiness Review — 15 Oct 2026", "Summary will separate decisions from information items.", d(2026, 10, 27), "Demo User"],
  ["A-016", project, "Confirm the document naming and versioning convention", "Configuration Lead", "Completed", d(2026, 10, 20), "", "A-024", "Flight Test Readiness Review — 15 Oct 2026", "Completed; convention recorded in the working register.", d(2026, 10, 27), "Demo User"],
  ["A-017", project, "Complete the initial systems integration baseline", "Systems Lead", "Completed", d(2026, 10, 10), "", "", "Baseline Review — 18 Sep 2026", "Historical action completed for linkage demonstration.", d(2026, 10, 10), "Demo User"],
  ["A-018", project, "Close the previous interface control document review", "Avionics Lead", "Completed", d(2026, 10, 12), "A-017", "", "Baseline Review — 18 Sep 2026", "Historical action completed for linkage demonstration.", d(2026, 10, 12), "Demo User"],
  ["A-019", project, "Confirm test equipment planning assumptions", "Test Manager", "Completed", d(2026, 10, 14), "A-017", "", "Baseline Review — 18 Sep 2026", "Historical action completed for linkage demonstration.", d(2026, 10, 14), "Demo User"],
  ["A-020", project, "Complete the prior ground-interface checklist review", "Ground Systems Lead", "Completed", d(2026, 10, 16), "A-017", "", "Ground Support Review — 22 Sep 2026", "Historical action completed for linkage demonstration.", d(2026, 10, 16), "Demo User"],
  ["A-021", project, "Record prior configuration assumptions for test facilities", "Facilities Lead", "Completed", d(2026, 10, 17), "", "", "Ground Support Review — 22 Sep 2026", "Historical action completed for linkage demonstration.", d(2026, 10, 17), "Demo User"],
  ["A-022", project, "Issue the previous integration schedule risk note", "Project Manager", "Completed", d(2026, 10, 18), "A-018", "", "Ground Support Review — 22 Sep 2026", "Historical action completed for linkage demonstration.", d(2026, 10, 18), "Demo User"],
  ["A-023", project, "Prepare the earlier readiness review data package", "Configuration Lead", "Completed", d(2026, 10, 19), "A-019", "", "Readiness Review — 25 Sep 2026", "Historical action completed for linkage demonstration.", d(2026, 10, 19), "Demo User"],
  ["A-024", project, "Record the previous document versioning decision", "Configuration Lead", "Completed", d(2026, 10, 21), "", "", "Readiness Review — 25 Sep 2026", "Historical action completed for linkage demonstration.", d(2026, 10, 21), "Demo User"],
];

const workbook = Workbook.create();
const dashboard = workbook.worksheets.add("Dashboard");
const register = workbook.worksheets.add("Action Register");
const audit = workbook.worksheets.add("Audit Log");
const readme = workbook.worksheets.add("Read Me");

for (const sheet of [dashboard, register, audit, readme]) {
  sheet.showGridLines = false;
}

// Action Register
register.getRange("A1:N1").values = [headers];
register.getRange(`A2:L${rows.length + 1}`).values = rows;
register.getRange("M2").formulas = [["=IF(F2=\"\",\"\",F2-Dashboard!$B$3)"]];
register.getRange(`M2:M${rows.length + 1}`).fillDown();
register.getRange("N2").formulas = [["=IF(E2=\"Completed\",\"Completed\",IF(E2=\"Cancelled\",\"Cancelled\",IF(F2=\"\",\"Missing due date\",IF(M2<0,\"Overdue\",IF(M2<=7,\"Critical\",IF(M2<=14,\"Action needed\",IF(M2<=21,\"Reminder\",\"On track\")))))))"]];
register.getRange(`N2:N${rows.length + 1}`).fillDown();
register.getRange(`F2:F${rows.length + 1}`).format.numberFormat = "yyyy-mm-dd";
register.getRange(`K2:K${rows.length + 1}`).format.numberFormat = "yyyy-mm-dd";
register.getRange(`M2:M${rows.length + 1}`).format.numberFormat = "0";
register.getRange("A1:N1").format = { fill: "#1F4E78", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center", wrapText: true };
register.getRange(`A2:N${rows.length + 1}`).format = { font: { name: "Arial", size: 10, color: "#1F2937" }, verticalAlignment: "center" };
register.getRange(`A1:N${rows.length + 1}`).format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
register.getRange(`A1:N${rows.length + 1}`).format.autofitColumns();
register.getRange("C:C").format.columnWidth = 42;
register.getRange("I:I").format.columnWidth = 34;
register.getRange("J:J").format.columnWidth = 38;
register.getRange("G:H").format.columnWidth = 24;
register.freezePanes.freezeRows(1);
register.tables.add(`A1:N${rows.length + 1}`, true, "ActionRegisterTable");
register.getRange(`E2:E${rows.length + 1}`).dataValidation = { rule: { type: "list", values: ["Not Started", "In Progress", "Blocked", "Completed", "Cancelled"] } };
register.getRange(`N2:N${rows.length + 1}`).conditionalFormats.add("containsText", { text: "Overdue", format: { fill: "#FECACA", font: { color: "#991B1B", bold: true } } });
register.getRange(`N2:N${rows.length + 1}`).conditionalFormats.add("containsText", { text: "Critical", format: { fill: "#FED7AA", font: { color: "#9A3412", bold: true } } });
register.getRange(`N2:N${rows.length + 1}`).conditionalFormats.add("containsText", { text: "Action needed", format: { fill: "#FEF3C7", font: { color: "#92400E", bold: true } } });
register.getRange(`N2:N${rows.length + 1}`).conditionalFormats.add("containsText", { text: "Reminder", format: { fill: "#DBEAFE", font: { color: "#1D4ED8", bold: true } } });
register.getRange(`E2:E${rows.length + 1}`).conditionalFormats.add("containsText", { text: "Blocked", format: { fill: "#FCE7F3", font: { color: "#9D174D", bold: true } } });

// Dashboard
dashboard.getRange("A1").values = [["Action Item Management Dashboard"]];
dashboard.getRange("A2").values = [["Synthetic single-project demonstration — edit the as-of date to refresh deadline indicators."]];
dashboard.getRange("A3").values = [["As-of date"]];
dashboard.getRange("B3").values = [[d(2026, 10, 27)]];
dashboard.getRange("B3").format.numberFormat = "yyyy-mm-dd";
dashboard.getRange("A1").format = { font: { name: "Arial", size: 16, bold: true, color: "#1F2937" } };
dashboard.getRange("A2").format = { font: { name: "Arial", size: 10, italic: true, color: "#4B5563" } };
dashboard.getRange("A3:B3").format = { font: { name: "Arial", size: 10, bold: true, color: "#1F2937" } };

const cardLabels = ["Total", "Outstanding", "Overdue", "Reminder", "Action needed", "Critical", "Blocked"];
const cardCols = ["A", "C", "E", "G", "I", "K", "M"];
const cardFormulas = [
  `=COUNTA('Action Register'!$A$2:$A$${rows.length + 1})`,
  `=COUNTIFS('Action Register'!$E$2:$E$${rows.length + 1},"<>Completed",'Action Register'!$E$2:$E$${rows.length + 1},"<>Cancelled")`,
  `=COUNTIF('Action Register'!$N$2:$N$${rows.length + 1},"Overdue")`,
  `=COUNTIF('Action Register'!$N$2:$N$${rows.length + 1},"Reminder")`,
  `=COUNTIF('Action Register'!$N$2:$N$${rows.length + 1},"Action needed")`,
  `=COUNTIF('Action Register'!$N$2:$N$${rows.length + 1},"Critical")`,
  `=COUNTIF('Action Register'!$E$2:$E$${rows.length + 1},"Blocked")`,
];
for (let i = 0; i < cardLabels.length; i++) {
  const col = cardCols[i];
  dashboard.getRange(`${col}5`).values = [[cardLabels[i]]];
  dashboard.getRange(`${col}6`).formulas = [[cardFormulas[i]]];
  dashboard.getRange(`${col}5`).format = { fill: "#E8EEF7", font: { name: "Arial", size: 10, bold: true, color: "#1F4E78" }, horizontalAlignment: "center" };
  dashboard.getRange(`${col}6`).format = { fill: "#F8FAFC", font: { name: "Arial", size: 18, bold: true, color: "#111827" }, horizontalAlignment: "center" };
}
dashboard.getRange("A5:N6").format.borders = { preset: "outside", style: "thin", color: "#CBD5E1" };

dashboard.getRange("A9:B9").values = [["Deadline band", "Count"]];
dashboard.getRange("A10:A15").values = [["Overdue"], ["Critical"], ["Action needed"], ["Reminder"], ["On track"], ["Missing due date"]];
dashboard.getRange("B10").formulas = [[`=COUNTIF('Action Register'!$N$2:$N$${rows.length + 1},A10)`]];
dashboard.getRange("B10:B15").fillDown();
dashboard.getRange("A9:B9").format = { fill: "#1F4E78", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
dashboard.getRange("A10:B15").format = { font: { name: "Arial", size: 10, color: "#1F2937" } };
dashboard.getRange("A9:B15").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };

dashboard.getRange("D9:E9").values = [["Status", "Count"]];
dashboard.getRange("D10:D14").values = [["Not Started"], ["In Progress"], ["Blocked"], ["Completed"], ["Cancelled"]];
dashboard.getRange("E10").formulas = [[`=COUNTIF('Action Register'!$E$2:$E$${rows.length + 1},D10)`]];
dashboard.getRange("E10:E14").fillDown();
dashboard.getRange("D9:E9").format = { fill: "#1F4E78", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
dashboard.getRange("D10:E14").format = { font: { name: "Arial", size: 10, color: "#1F2937" } };
dashboard.getRange("D9:E14").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };

dashboard.getRange("G9:L9").values = [["What the dashboard supports", "", "", "", "", ""]];
dashboard.getRange("G10:G15").values = [
  ["Track outstanding actions"],
  ["Show approaching and overdue deadlines"],
  ["Display explicit dependencies"],
  ["Link current actions to past actions"],
  ["Draft reminders and key points"],
  ["Archive older workbook versions before overwrite"],
];
dashboard.getRange("G9:L9").format = { fill: "#1F4E78", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" } };
dashboard.getRange("G10:L15").format = { font: { name: "Arial", size: 10, color: "#1F2937" } };
dashboard.getRange("G9:L15").format.borders = { preset: "outside", style: "thin", color: "#D9E2F3" };

dashboard.getRange("A18:F18").values = [["Attention items", "", "", "", "", ""]];
dashboard.getRange("A19:F19").values = [["Action ID", "Description", "Owner", "Status", "Due date", "Deadline band"]];
const attentionIds = ["A-003", "A-008", "A-015", "A-002", "A-009", "A-010"];
for (let i = 0; i < attentionIds.length; i++) {
  const row = 20 + i;
  const sourceRow = 2 + rows.findIndex((r) => r[0] === attentionIds[i]);
  dashboard.getRange(`A${row}`).formulas = [[`='Action Register'!A${sourceRow}`]];
  dashboard.getRange(`B${row}`).formulas = [[`='Action Register'!C${sourceRow}`]];
  dashboard.getRange(`C${row}`).formulas = [[`='Action Register'!D${sourceRow}`]];
  dashboard.getRange(`D${row}`).formulas = [[`='Action Register'!E${sourceRow}`]];
  dashboard.getRange(`E${row}`).formulas = [[`='Action Register'!F${sourceRow}`]];
  dashboard.getRange(`F${row}`).formulas = [[`='Action Register'!N${sourceRow}`]];
}
dashboard.getRange("A18:F18").format = { fill: "#1F4E78", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" } };
dashboard.getRange("A19:F19").format = { fill: "#DCE6F1", font: { name: "Arial", size: 10, bold: true, color: "#1F2937" }, horizontalAlignment: "center", wrapText: true };
dashboard.getRange("A20:F25").format = { font: { name: "Arial", size: 10, color: "#1F2937" } };
dashboard.getRange("E20:E25").format.numberFormat = "yyyy-mm-dd";
dashboard.getRange("A18:F25").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };

dashboard.getRange("A28:N29").values = [["Human review required", "AI-suggested historical links and follow-up drafts are not confirmed facts. Review before recording or communicating.", "", "", "", "", "", "", "", "", "", "", "", ""], ["Security boundary", "This workbook uses synthetic demonstration data. Classified use requires the approved on-premises environment and API.", "", "", "", "", "", "", "", "", "", "", "", ""]];
dashboard.getRange("A28:A29").format = { fill: "#FEF3C7", font: { name: "Arial", size: 10, bold: true, color: "#92400E" } };
dashboard.getRange("B28:N29").format = { fill: "#FFFBEB", font: { name: "Arial", size: 10, color: "#78350F" }, wrapText: true };

dashboard.getRange("A:N").format.columnWidth = 14;
dashboard.getRange("A:A").format.columnWidth = 24;
dashboard.getRange("B:B").format.columnWidth = 42;
dashboard.getRange("G:L").format.columnWidth = 18;
dashboard.getRange("A1:N29").format.verticalAlignment = "center";

// Audit Log and Read Me
audit.getRange("A1:F2").values = [
  ["Timestamp", "User", "Action ID", "Field", "Previous value", "New value"],
  [d(2026, 10, 27), "Demo User", "", "", "", "Synthetic demonstration workbook created"],
];
audit.getRange("A1:F1").format = { fill: "#1F4E78", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
audit.getRange("A2:F2").format = { font: { name: "Arial", size: 10, color: "#1F2937" } };
audit.getRange("A2:A2").format.numberFormat = "yyyy-mm-dd";
audit.getRange("A1:F2").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
audit.getRange("A:F").format.columnWidth = 22;

readme.getRange("A1:B10").values = [
  ["Item", "Definition"],
  ["Workbook purpose", "Editable action register and dashboard for one synthetic project."],
  ["Source of truth", "Action Register sheet in the working Excel file."],
  ["Deadline logic", "15–21 days Reminder; 8–14 days Action needed; 0–7 days Critical; passed due date Overdue."],
  ["Blocked", "The action cannot progress because of an unresolved dependency, decision, resource, access or external constraint."],
  ["Traceability", "The dashboard records the update user and field-level previous/new values when changes are saved."],
  ["Rollback", "The previous working workbook is archived before overwrite. Restore is an authorised operational step."],
  ["AI boundary", "The on-premises AI API is optional and replaceable. Deterministic fallback is used when it is not connected."],
  ["Communication", "Reminder and key-point outputs are drafts only. Nothing is sent automatically."],
  ["Security", "This file contains synthetic demonstration data. Do not use classified information outside the approved environment."],
];
readme.getRange("A1:B1").format = { fill: "#1F4E78", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
readme.getRange("A2:B10").format = { font: { name: "Arial", size: 10, color: "#1F2937" }, wrapText: true };
readme.getRange("A1:B10").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
readme.getRange("A:A").format.columnWidth = 24;
readme.getRange("B:B").format.columnWidth = 92;

workbook.recalculate();

const dashboardInspect = await workbook.inspect({ kind: "table", range: "Dashboard!A1:N29", include: "values,formulas", tableMaxRows: 30, tableMaxCols: 14, maxChars: 12000 });
console.log(dashboardInspect.ndjson);
const registerInspect = await workbook.inspect({ kind: "table", range: "Action Register!A1:N8", include: "values,formulas", tableMaxRows: 8, tableMaxCols: 14, maxChars: 8000 });
console.log(registerInspect.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan" });
console.log(errors.ndjson);

const preview = await workbook.render({ sheetName: "Dashboard", autoCrop: "all", scale: 1, format: "png" });
await fs.writeFile(`${outputDir}/dashboard_preview.png`, new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(`${outputDir}/action_register_demo.xlsx`);
