import json
from datetime import date

import pytest

from vehicle_maintenance.invoice import audit_invoice
from vehicle_maintenance.migration import migrate_records, sha256_file
from vehicle_maintenance.mutations import preview_or_commit
from vehicle_maintenance.quotes import quote_packet
from vehicle_maintenance.repository import (
    add_benchmark,
    add_quote,
    add_shop,
    bootstrap_vehicle,
    create_plan,
    quote_comparison,
    record_reading,
    seed_august_2026_event,
    service_history,
    status,
)


def test_vehicle_status_plan_quotes_and_history(tmp_path):
    database = tmp_path / "maintenance.sqlite3"
    assert bootstrap_vehicle(database)["created"]
    assert not bootstrap_vehicle(database)["created"]
    reading = record_reading(
        {"odometer_miles": 8462, "minder_code": "A67", "captured_at": "2026-08-15T08:00:00"},
        database,
    )
    assert reading["reading_id"] == 1
    event = seed_august_2026_event(database)
    assert event["total_cents"] == 60521
    assert not seed_august_2026_event(database)["created"]
    current = status(database)
    assert current["last_service"]["total_cents"] == 60521
    assert service_history(database)[0]["line_items"][2]["total_cents"] == 32801

    plan = create_plan("A67", 8462, database=database)
    assert plan["service_codes"] == ["A", "6", "7"]
    for index, category in enumerate(["dealer", "dealer", "specialist", "specialist", "specialist"]):
        add_shop(
            {
                "id": f"shop-{index}",
                "name": f"Synthetic shop {index}",
                "category": category,
                "distance_miles": 5 + index,
                "honda_hybrid_experience": 0.8,
                "source_url": "https://example.com/shop",
                "verified_at": "2026-08-15",
            },
            database,
        )
    packet = quote_packet(plan["plan_id"], database)
    assert packet["complete"]
    assert len(packet["requests"]) == 5
    for index in range(3):
        add_quote(
            {
                "id": f"quote-{index}",
                "shop_id": f"shop-{index}",
                "plan_id": plan["plan_id"],
                "received_at": date(2026, 8, 15).isoformat(),
                "out_the_door_cents": 16000 + index * 1000,
                "warranty_score": 0.8,
                "travel_minutes": 20,
                "completeness_score": 1,
                "honda_hybrid_experience": 0.8,
            },
            database,
        )
    assert quote_comparison(plan["plan_id"], database)["best_value_declared"]
    assert quote_comparison("ACTIVE", database)["best_quote_id"] == "quote-0"
    with pytest.raises(ValueError, match="not found"):
        quote_comparison("missing", database)


def test_verified_migration_keeps_source_and_links_invoice(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    document = source / "synthetic-invoice.jpg"
    document.write_bytes(b"synthetic reviewed bytes")
    destination = tmp_path / "private-store"
    result = migrate_records(source, destination=destination)
    assert document.exists()
    assert result["file_count"] == 1
    copied = destination / "documents" / "maintenance-records" / document.name
    assert copied.exists()
    assert sha256_file(copied) == sha256_file(document)
    assert audit_invoice(copied, destination / "maintenance.sqlite3")["passed"]
    manifest = json.loads((destination / "backups").glob("import-manifest-*.json").__next__().read_text())
    assert manifest["source_left_untouched"]
    assert manifest["event"]["total_cents"] == 60521


def test_mutation_preview_commit_and_guard(tmp_path):
    database = tmp_path / "maintenance.sqlite3"
    settings = tmp_path / "settings.json"
    payload = {"odometer_miles": 9000, "minder_code": "A"}
    preview = preview_or_commit("add_reading", payload, database=database, settings_path=settings)
    assert not preview.commit
    assert preview.confirmation_token
    committed = preview_or_commit(
        "add_reading",
        payload,
        commit=True,
        confirmation_token=preview.confirmation_token,
        database=database,
        settings_path=settings,
    )
    assert committed.commit
    assert committed.result["reading_id"] == 1
    with pytest.raises(ValueError, match="requires"):
        preview_or_commit("add_reading", payload, commit=True, database=database, settings_path=settings)
    with pytest.raises(ValueError, match="unsupported"):
        preview_or_commit("send_message", payload, database=database, settings_path=settings)


def test_cost_benchmark_validation(tmp_path):
    database = tmp_path / "maintenance.sqlite3"
    result = add_benchmark(
        {
            "service_code": "7",
            "market": "US online estimate; not a local quote",
            "low_cents": 11000,
            "median_cents": 13550,
            "high_cents": 16100,
            "retrieved_at": "2026-08-15",
            "source_url": "https://example.com/synthetic-benchmark",
        },
        database,
    )
    assert result["benchmark_id"] == 1
    with pytest.raises(ValueError, match="low <= median"):
        add_benchmark(
            {
                "service_code": "7",
                "market": "synthetic",
                "low_cents": 200,
                "median_cents": 100,
                "high_cents": 300,
                "source_url": "https://example.com",
            },
            database,
        )
