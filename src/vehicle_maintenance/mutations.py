"""Local-only mutations shared by MCP tools after explicit confirmation."""

from __future__ import annotations

import shutil
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from .confirmation import issue_preview, validate_token
from .db import AuthorizationRow, DocumentRow, ServiceEventRow, ServiceLineItemRow, session_scope
from .migration import sha256_file
from .models import MutationPreview
from .paths import data_paths
from .repository import add_quote, record_reading


def _import_document(payload: dict[str, object], database: str | Path | None = None) -> dict[str, object]:
    source = Path(str(payload["path"])).expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"document does not exist: {source}")
    if not bool(payload.get("reviewed")):
        raise ValueError("document imports must be marked reviewed")
    paths = data_paths().ensure()
    checksum = sha256_file(source)
    target = paths.documents / "reviewed-imports" / f"{checksum[:12]}-{source.name}"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(source, target)
    with session_scope(database) as session:
        row = DocumentRow(
            id=f"doc-{checksum[:16]}",
            event_id=str(payload["event_id"]) if payload.get("event_id") else None,
            original_name=source.name,
            sha256=checksum,
            local_path=str(target),
            reviewed=True,
            extracted_text_path=None,
        )
        session.merge(row)
    return {"document_id": row.id, "sha256": checksum, "private_path": str(target)}


def _record_authorization(payload: dict[str, object], database: str | Path | None = None) -> dict[str, object]:
    with session_scope(database) as session:
        if session.get(ServiceEventRow, str(payload["event_id"])) is None:
            raise ValueError("authorization can only record an existing local event")
        row = AuthorizationRow(
            event_id=str(payload["event_id"]),
            recorded_at=datetime.fromisoformat(str(payload.get("recorded_at", datetime.now().isoformat()))),
            decision=str(payload["decision"]),
            amount_cents=int(payload["amount_cents"]) if payload.get("amount_cents") is not None else None,
            evidence=str(payload["evidence"]),
        )
        session.add(row)
        session.flush()
        return {"authorization_record_id": row.id, "external_action_taken": False}


def _complete_event(payload: dict[str, object], database: str | Path | None = None) -> dict[str, object]:
    event_id = str(payload.get("id") or f"service-{date.today().isoformat()}-{uuid4().hex[:6]}")
    with session_scope(database) as session:
        if session.get(ServiceEventRow, event_id):
            raise ValueError(f"service event already exists: {event_id}")
        event = ServiceEventRow(
            id=event_id,
            vehicle_id=str(payload["vehicle_id"]),
            service_date=date.fromisoformat(str(payload["service_date"])),
            odometer_miles=int(payload["odometer_miles"]),
            displayed_code=str(payload["displayed_code"]) if payload.get("displayed_code") else None,
            total_cents=int(payload["total_cents"]),
            provider_name=str(payload["provider_name"]) if payload.get("provider_name") else None,
            notes=str(payload["notes"]) if payload.get("notes") else None,
        )
        event.line_items = [
            ServiceLineItemRow(
                description=str(item["description"]),
                labor_cents=int(item.get("labor_cents", 0)),
                parts_cents=int(item.get("parts_cents", 0)),
                fees_cents=int(item.get("fees_cents", 0)),
                tax_cents=int(item.get("tax_cents", 0)),
                total_cents=int(item["total_cents"]),
                maintenance_codes=",".join(item.get("maintenance_codes", [])),
            )
            for item in payload.get("line_items", [])
        ]
        session.add(event)
    return {"event_id": event_id, "external_action_taken": False}


MUTATIONS = {
    "add_reading": record_reading,
    "import_reviewed_document": _import_document,
    "record_quote": add_quote,
    "record_authorization": _record_authorization,
    "complete_service_event": _complete_event,
}


def preview_or_commit(
    operation: str,
    payload: dict[str, object],
    *,
    commit: bool = False,
    confirmation_token: str | None = None,
    database: str | Path | None = None,
    settings_path: Path | None = None,
) -> MutationPreview:
    if operation not in MUTATIONS:
        raise ValueError(f"unsupported mutation: {operation}")
    if not commit:
        return issue_preview(operation, payload, settings_path=settings_path)
    if not confirmation_token:
        raise ValueError("commit=true requires the preview confirmation token")
    validate_token(operation, payload, confirmation_token, settings_path=settings_path)
    result = MUTATIONS[operation](payload, database)
    return MutationPreview(operation=operation, payload=payload, commit=True, result=result)
