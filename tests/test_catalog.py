from datetime import date

import pytest
from pydantic import ValidationError

from vehicle_maintenance.catalog import expand_minder_code, explain_minder_code, load_catalog
from vehicle_maintenance.models import CostBenchmark


def test_catalog_has_all_public_codes_and_citations():
    catalog = load_catalog()
    assert set(catalog) == {"A", "B", "1", "2", "3", "4", "5", "6", "7"}
    assert all(rule.market == "US" for rule in catalog.values())
    assert all(str(rule.source_url).startswith("https://techinfo.honda.com/") for rule in catalog.values())


@pytest.mark.parametrize(
    ("displayed", "expected"),
    [("A67", ["A", "6", "7"]), ("b 1, 2", ["B", "1", "2"]), ("7", ["7"])],
)
def test_expand_minder_code(displayed, expected):
    assert expand_minder_code(displayed) == expected
    assert [rule.code for rule in explain_minder_code(displayed)] == expected


def test_unknown_code_is_rejected():
    with pytest.raises(ValueError, match="unrecognized"):
        expand_minder_code("oil maybe")


def test_benchmark_ranges_are_ordered():
    valid = CostBenchmark(
        service_code="7",
        market="Seattle, WA",
        low_cents=10000,
        median_cents=16000,
        high_cents=33000,
        retrieved_at=date(2026, 8, 15),
        source_url="https://example.com/benchmark",
    )
    assert valid.median_cents == 16000
    with pytest.raises(ValidationError, match="benchmark range"):
        valid.model_copy(update={"low_cents": 20000, "median_cents": 10000}).model_validate(
            valid.model_copy(update={"low_cents": 20000, "median_cents": 10000}).model_dump()
        )
