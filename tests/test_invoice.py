import json
from pathlib import Path

import pytest

from vehicle_maintenance.invoice import audit_invoice, audit_invoice_payload, august_2026_invoice_fixture


def test_august_invoice_reproduces_total():
    result = audit_invoice_payload(august_2026_invoice_fixture())
    assert result["passed"]
    assert result["checks"]["reported_total_cents"] == 60521
    assert result["checks"]["summary_sum_cents"] == 60521


def test_json_invoice_and_mismatch(tmp_path):
    payload = august_2026_invoice_fixture()
    payload["total_cents"] = 1
    target = tmp_path / "invoice.json"
    target.write_text(json.dumps(payload))
    assert not audit_invoice(target)["passed"]
    with pytest.raises(ValueError, match="not a file"):
        audit_invoice(tmp_path / "missing.json")


def test_unlinked_document_requires_review(tmp_path):
    target = tmp_path / "invoice.jpg"
    target.write_bytes(b"synthetic non-image bytes")
    result = audit_invoice(target, tmp_path / "maintenance.sqlite3")
    assert result["needs_review"]
    assert len(result["document_sha256"]) == 64


def test_bundled_synthetic_invoice():
    path = Path(__file__).parent / "fixtures" / "synthetic" / "invoice-a67.json"
    assert audit_invoice(path)["passed"]
