from datetime import UTC, datetime, timedelta

import pytest

from vehicle_maintenance.confirmation import issue_preview, validate_token


def test_token_is_payload_and_operation_bound_and_expires(tmp_path):
    settings = tmp_path / "settings.json"
    now = datetime(2026, 8, 15, tzinfo=UTC)
    payload = {"odometer_miles": 8462, "minder_code": "A67"}
    preview = issue_preview("add_reading", payload, settings_path=settings, now=now)
    assert preview.confirmation_token
    validate_token("add_reading", payload, preview.confirmation_token, settings_path=settings, now=now)
    with pytest.raises(ValueError, match="different payload"):
        validate_token(
            "add_reading",
            {**payload, "odometer_miles": 1},
            preview.confirmation_token,
            settings_path=settings,
            now=now,
        )
    with pytest.raises(ValueError, match="different operation"):
        validate_token("record_quote", payload, preview.confirmation_token, settings_path=settings, now=now)
    with pytest.raises(ValueError, match="expired"):
        validate_token(
            "add_reading",
            payload,
            preview.confirmation_token,
            settings_path=settings,
            now=now + timedelta(minutes=6),
        )


def test_bad_token_rejected(tmp_path):
    with pytest.raises(ValueError, match="malformed"):
        validate_token("add_reading", {}, "bad", settings_path=tmp_path / "settings.json")
