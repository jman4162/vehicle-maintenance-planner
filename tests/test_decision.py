import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from vehicle_maintenance.decision import calculate_break_even, compare_quotes, recommend_decision
from vehicle_maintenance.models import Decision, Quote


def parity_fixture():
    return json.loads((Path(__file__).parent / "shared" / "decision-parity.json").read_text())


def test_break_even_matches_shared_fixture():
    fixture = parity_fixture()["break_even"]
    result = calculate_break_even(fixture["dealer_cents"], fixture["alternative_cents"])
    assert result.savings_cents == fixture["expected_savings_cents"]
    assert result.break_even_hours == fixture["expected_hours"]


def test_break_even_handles_no_savings_and_invalid_prices():
    result = calculate_break_even(10000, 12000)
    assert result.savings_cents == -2000
    assert set(result.break_even_hours.values()) == {0.0}
    with pytest.raises(ValueError, match="non-negative"):
        calculate_break_even(-1, 10)


def test_quote_ranking_requires_three_current_comparable_quotes():
    quotes = [Quote.model_validate(item) for item in parity_fixture()["quotes"]]
    result = compare_quotes(quotes, as_of=date(2026, 8, 15))
    assert result.best_value_declared
    assert result.best_quote_id == "quote-specialist-a"
    assert result.comparable_current_count == 3

    stale = quotes[0].model_copy(update={"received_at": date(2026, 8, 15) - timedelta(days=31)})
    incomplete = compare_quotes([stale, *quotes[1:]], as_of=date(2026, 8, 15))
    assert not incomplete.best_value_declared
    assert incomplete.best_quote_id is None
    assert any(item.stale for item in incomplete.ranked)


def test_ineligible_quote_and_decision_branches():
    quote = Quote.model_validate(parity_fixture()["quotes"][0]).model_copy(
        update={"written": False, "comparable_scope": False}
    )
    result = compare_quotes([quote], as_of=date(2026, 8, 15))
    assert not result.ranked[0].eligible
    assert len(result.ranked[0].reasons) == 2
    assert (
        recommend_decision(
            safety_uncertainty=True,
            missing_scope_or_fees=False,
            due_now=False,
            alternative_saves=True,
            extra_trip_hours=1,
            break_even_hours=2,
        )
        == Decision.SAFETY_ADVICE
    )
    assert (
        recommend_decision(
            safety_uncertainty=False,
            missing_scope_or_fees=True,
            due_now=False,
            alternative_saves=True,
            extra_trip_hours=1,
            break_even_hours=2,
        )
        == Decision.CLARIFY
    )
    assert (
        recommend_decision(
            safety_uncertainty=False,
            missing_scope_or_fees=False,
            due_now=False,
            alternative_saves=True,
            extra_trip_hours=1,
            break_even_hours=2,
        )
        == Decision.DEFER_AND_QUOTE
    )
    assert (
        recommend_decision(
            safety_uncertainty=False,
            missing_scope_or_fees=False,
            due_now=True,
            alternative_saves=True,
            extra_trip_hours=1,
            break_even_hours=2,
        )
        == Decision.AUTHORIZE_NOW
    )
