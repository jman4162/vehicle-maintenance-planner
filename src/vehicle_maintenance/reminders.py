"""Portable calendar reminders without sending or booking anything."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from .paths import data_paths
from .repository import resolve_plan


def _stamp(value: datetime) -> str:
    return value.strftime("%Y%m%dT%H%M%S")


def export_reminders(
    plan_id: str,
    appointment: datetime,
    *,
    database: str | Path | None = None,
    output: str | Path | None = None,
) -> Path:
    plan = resolve_plan(plan_id, database)
    created = datetime.now()
    events = [
        (
            f"{plan.id}-quotes",
            appointment - timedelta(days=7),
            "Gather written vehicle-maintenance quotes",
            "Request identical itemized scope; collect at least three current comparable quotes.",
        ),
        (
            f"{plan.id}-packet",
            appointment - timedelta(days=1),
            "Export offline maintenance decision packet",
            "Review due sources, quotes, benchmarks, and extra-trip assumptions before the appointment.",
        ),
        (
            f"{plan.id}-appointment",
            appointment,
            "Vehicle maintenance appointment",
            "Review the written estimate and authorization before work. This calendar file does not book service.",
        ),
    ]
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Vehicle Maintenance Planner//EN"]
    for uid, start, summary, description in events:
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}@vehicle-maint.local",
                f"DTSTAMP:{_stamp(created)}",
                f"DTSTART:{_stamp(start)}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{description}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    target = Path(output) if output else data_paths().ensure().exports / f"reminders-{plan.id}.ics"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return target
