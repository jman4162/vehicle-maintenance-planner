import json
from pathlib import Path

import pytest

from vehicle_maintenance.packet import (
    build_decision_packet,
    decrypt_packet,
    encrypt_packet,
    export_decision_packet,
    import_decision_packet,
)
from vehicle_maintenance.repository import create_plan


def test_encrypted_packet_round_trip_and_authentication():
    payload = {"schema_version": 1, "plan": {"id": "synthetic"}}
    envelope = encrypt_packet(payload, "correct horse battery staple")
    assert "synthetic" not in envelope["ciphertext"]
    assert decrypt_packet(envelope, "correct horse battery staple") == payload
    with pytest.raises(ValueError, match="authentication failed"):
        decrypt_packet(envelope, "incorrect but long passphrase")
    with pytest.raises(ValueError, match="12 characters"):
        encrypt_packet(payload, "short")
    with pytest.raises(ValueError, match="unsupported"):
        decrypt_packet({**envelope, "version": 2}, "correct horse battery staple")


def test_build_export_and_import_on_site_decision(tmp_path):
    database = tmp_path / "maintenance.sqlite3"
    plan = create_plan("A67", 8462, database=database)
    payload = build_decision_packet(plan["plan_id"], database)
    assert payload["plan"]["service_codes"] == ["A", "6", "7"]
    assert len(payload["catalog"]) == 9
    target = tmp_path / "packet.encrypted.json"
    export_decision_packet(
        "correct horse battery staple",
        plan_id=plan["plan_id"],
        database=database,
        output=target,
    )
    envelope = json.loads(target.read_text())
    phone_payload = decrypt_packet(envelope, "correct horse battery staple")
    phone_payload["on_site"] = {
        "support_state": "clarify_before_authorizing",
        "dealer_cents": 32801,
    }
    target.write_text(json.dumps(encrypt_packet(phone_payload, "correct horse battery staple")))
    result = import_decision_packet(target, "correct horse battery staple", database=database)
    assert result["support_state"] == "clarify_before_authorizing"
    assert not result["external_action_taken"]


def test_import_rejects_packet_without_reviewed_decision(tmp_path):
    database = tmp_path / "maintenance.sqlite3"
    plan = create_plan("A", 1, database=database)
    target = tmp_path / "packet.json"
    envelope = encrypt_packet(build_decision_packet(plan["plan_id"], database), "a valid passphrase")
    target.write_text(json.dumps(envelope))
    with pytest.raises(ValueError, match="on-site decision"):
        import_decision_packet(target, "a valid passphrase", database=database)


def test_shared_python_envelope_remains_readable():
    fixture = json.loads((Path(__file__).parent / "shared" / "python-encrypted-packet.json").read_text())
    assert decrypt_packet(fixture["envelope"], fixture["passphrase_for_test_only"]) == fixture["expected"]
