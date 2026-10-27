import unittest
from datetime import date

import pandas as pd

from action_dashboard_core import (
    add_deadline_fields,
    classify_deadline,
    compare_registers,
    dashboard_metrics,
)


class ActionDashboardTests(unittest.TestCase):
    def test_deadline_bands(self):
        as_of = date(2026, 10, 27)
        self.assertEqual(classify_deadline(date(2026, 11, 17), as_of)[1], "Reminder")
        self.assertEqual(classify_deadline(date(2026, 11, 10), as_of)[1], "Action needed")
        self.assertEqual(classify_deadline(date(2026, 11, 3), as_of)[1], "Critical")
        self.assertEqual(classify_deadline(date(2026, 10, 26), as_of)[1], "Overdue")

    def test_metrics(self):
        data = pd.DataFrame(
            {
                "Action ID": ["A-001", "A-002", "A-003"],
                "Status": ["In Progress", "Blocked", "Completed"],
                "Due date": [date(2026, 11, 10), date(2026, 10, 26), date(2026, 12, 1)],
            }
        )
        enriched = add_deadline_fields(data, date(2026, 10, 27))
        metrics = dashboard_metrics(enriched)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["outstanding"], 2)
        self.assertEqual(metrics["overdue"], 1)
        self.assertEqual(metrics["blocked"], 1)

    def test_completed_action_is_not_overdue(self):
        data = pd.DataFrame(
            {
                "Action ID": ["A-001", "A-002"],
                "Status": ["Completed", "In Progress"],
                "Due date": [date(2026, 10, 1), date(2026, 10, 1)],
            }
        )
        enriched = add_deadline_fields(data, date(2026, 10, 27))
        self.assertEqual(enriched.loc[0, "Deadline band"], "Completed")
        self.assertEqual(enriched.loc[1, "Deadline band"], "Overdue")

    def test_change_tracking(self):
        before = pd.DataFrame({"Action ID": ["A-001"], "Status": ["In Progress"]})
        after = pd.DataFrame({"Action ID": ["A-001"], "Status": ["Completed"]})
        changes = compare_registers(before, after)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["Field"], "Status")
        self.assertEqual(changes[0]["Previous value"], "In Progress")
        self.assertEqual(changes[0]["New value"], "Completed")


if __name__ == "__main__":
    unittest.main()
