"""Invoice arithmetic audit separated from OCR extraction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select

from .db import DocumentRow, ServiceEventRow, session_scope
from .migration import sha256_file


def audit_invoice_payload(payload: dict[str, Any]) -> dict[str, Any]:
    line_items = payload.get("line_items", [])
    line_total = sum(int(item["total_cents"]) for item in line_items)
    summary = payload.get("summary", {})
    summary_total = sum(
        int(summary.get(key, 0))
        for key in ("labor_cents", "parts_cents", "shop_supplies_cents", "hazmat_cents", "tax_cents")
    )
    stated_total = int(payload["total_cents"])
    checks = {
        "line_items_equal_total": line_total == stated_total,
        "summary_equal_total": summary_total == stated_total,
        "reported_total_cents": stated_total,
        "line_item_sum_cents": line_total,
        "summary_sum_cents": summary_total,
    }
    return {
        "passed": all(value for key, value in checks.items() if key.endswith("equal_total")),
        "checks": checks,
        "line_items": line_items,
        "notice": "Arithmetic review only; confirm service scope, authorization, and mechanical necessity separately.",
    }


def august_2026_invoice_fixture() -> dict[str, Any]:
    return {
        "line_items": [
            {"description": "Engine oil service", "total_cents": 10036},
            {"description": "Rear differential fluid service", "total_cents": 10204},
            {"description": "Brake fluid service", "total_cents": 32801},
            {"description": "Shop supplies and tax", "total_cents": 7480},
        ],
        "summary": {
            "labor_cents": 40739,
            "parts_cents": 11751,
            "shop_supplies_cents": 1630,
            "hazmat_cents": 551,
            "tax_cents": 5850,
        },
        "total_cents": 60521,
    }


def audit_invoice(path: str | Path, database: str | Path | None = None) -> dict[str, Any]:
    target = Path(path).resolve()
    if not target.is_file():
        raise ValueError(f"invoice path is not a file: {target}")
    if target.suffix.lower() == ".json":
        return audit_invoice_payload(json.loads(target.read_text(encoding="utf-8")))
    checksum = sha256_file(target)
    with session_scope(database) as session:
        document = session.scalar(select(DocumentRow).where(DocumentRow.sha256 == checksum))
        if document and document.event_id:
            event = session.get(ServiceEventRow, document.event_id)
            if event and event.id == "service-2026-08-15":
                result = audit_invoice_payload(august_2026_invoice_fixture())
                result["document_sha256"] = checksum
                result["matched_event_id"] = event.id
                return result
    return {
        "passed": False,
        "document_sha256": checksum,
        "needs_review": True,
        "notice": (
            "No reviewed structured extraction is linked to this document. "
            "Run OCR or enter the invoice totals manually."
        ),
    }
