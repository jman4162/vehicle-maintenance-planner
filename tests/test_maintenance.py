from datetime import date

from vehicle_maintenance.catalog import load_catalog
from vehicle_maintenance.maintenance import assess_displayed_code, assess_rule, assess_time_fallbacks
from vehicle_maintenance.models import DueState, Origin


def test_displayed_origin_is_distinct_from_dealer_recommendation():
    displayed = assess_displayed_code("A67")
    assert {item.state for item in displayed} == {DueState.DUE_NOW}
    dealer = assess_rule(
        load_catalog()["7"],
        displayed=False,
        origin=Origin.DEALER_RECOMMENDED,
    )
    assert dealer.state == DueState.DEALER_RECOMMENDED
    assert "does not establish" in dealer.reason


def test_time_fallbacks_use_month_precision_without_mileage_schedule():
    assessments = assess_time_fallbacks(
        as_of=date(2026, 8, 15),
        purchase_month=date(2023, 9, 1),
    )
    by_code = {item.code: item for item in assessments}
    assert by_code["7"].state == DueState.DUE_SOON
    assert by_code["A"].state == DueState.TIME_DUE
    assert "mileage" not in by_code["7"].reason


def test_unknown_and_forecast_states():
    rule = load_catalog()["6"]
    assert assess_rule(rule, displayed=False, origin=Origin.USER_REQUESTED).state == DueState.UNKNOWN
    oil = load_catalog()["A"]
    result = assess_rule(
        oil,
        displayed=False,
        origin=Origin.USER_REQUESTED,
        as_of=date(2026, 1, 1),
        last_completed=date(2025, 8, 1),
    )
    assert result.state == DueState.FORECAST
