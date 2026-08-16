"""Due-state assessment without invented mileage schedules."""

from __future__ import annotations

from datetime import date

from .catalog import explain_minder_code, load_catalog
from .models import DueAssessment, DueState, MaintenanceRule, Origin


def _months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + end.month - start.month


def assess_rule(
    rule: MaintenanceRule,
    *,
    displayed: bool,
    origin: Origin,
    as_of: date | None = None,
    last_completed: date | None = None,
    purchase_month: date | None = None,
) -> DueAssessment:
    if origin == Origin.DEALER_RECOMMENDED:
        return DueAssessment(
            code=rule.code,
            state=DueState.DEALER_RECOMMENDED,
            reason="A provider recommended this item; that does not establish a vehicle-displayed code.",
            rule=rule,
        )
    if displayed and origin == Origin.VEHICLE_DISPLAYED:
        return DueAssessment(
            code=rule.code,
            state=DueState.DUE_NOW,
            reason="The vehicle displayed this Maintenance Minder code.",
            rule=rule,
        )
    anchor = last_completed or purchase_month
    if rule.time_fallback_months and anchor:
        elapsed = _months_between(anchor, as_of or date.today())
        remaining = rule.time_fallback_months - elapsed
        if remaining <= 0:
            return DueAssessment(
                code=rule.code,
                state=DueState.TIME_DUE,
                reason=f"The cited {rule.time_fallback_months}-month fallback has elapsed.",
                rule=rule,
            )
        if remaining <= 6:
            return DueAssessment(
                code=rule.code,
                state=DueState.DUE_SOON,
                reason=f"The cited time fallback is approximately {remaining} month(s) away.",
                rule=rule,
            )
        return DueAssessment(
            code=rule.code,
            state=DueState.FORECAST,
            reason=f"The cited time fallback is approximately {remaining} month(s) away.",
            rule=rule,
        )
    return DueAssessment(
        code=rule.code,
        state=DueState.UNKNOWN,
        reason="No vehicle-displayed code or cited time fallback establishes a due date.",
        rule=rule,
    )


def assess_displayed_code(
    displayed_code: str,
    *,
    origin: Origin = Origin.VEHICLE_DISPLAYED,
) -> list[DueAssessment]:
    return [assess_rule(rule, displayed=True, origin=origin) for rule in explain_minder_code(displayed_code)]


def assess_time_fallbacks(
    *,
    as_of: date,
    purchase_month: date,
    last_completed: dict[str, date] | None = None,
) -> list[DueAssessment]:
    completed = last_completed or {}
    return [
        assess_rule(
            rule,
            displayed=False,
            origin=Origin.USER_REQUESTED,
            as_of=as_of,
            last_completed=completed.get(rule.code),
            purchase_month=purchase_month,
        )
        for rule in load_catalog().values()
        if rule.time_fallback_months
    ]
