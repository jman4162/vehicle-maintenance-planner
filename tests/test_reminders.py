from datetime import datetime

from vehicle_maintenance.reminders import export_reminders
from vehicle_maintenance.repository import create_plan


def test_reminder_export_contains_three_local_events(tmp_path):
    database = tmp_path / "maintenance.sqlite3"
    plan = create_plan("A67", 8462, database=database)
    target = export_reminders(
        plan["plan_id"],
        datetime(2026, 9, 1, 9, 0),
        database=database,
        output=tmp_path / "reminders.ics",
    )
    text = target.read_text()
    assert text.count("BEGIN:VEVENT") == 3
    assert "Gather written vehicle-maintenance quotes" in text
    assert "does not book service" in text
