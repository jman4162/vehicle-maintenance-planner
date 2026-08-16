"""Encrypted JSON handoff compatible with the static PWA's Web Crypto format."""

from __future__ import annotations

import base64
import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import select

from .catalog import load_catalog
from .db import BenchmarkRow, DecisionPacketRow, QuoteRow, session_scope
from .paths import data_paths
from .repository import resolve_plan

ITERATIONS = 250_000


def _key(passphrase: str, salt: bytes) -> bytes:
    if len(passphrase) < 12:
        raise ValueError("passphrase must contain at least 12 characters")
    return PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    ).derive(passphrase.encode())


def encrypt_packet(payload: dict[str, Any], passphrase: str) -> dict[str, Any]:
    salt = secrets.token_bytes(16)
    iv = secrets.token_bytes(12)
    ciphertext = AESGCM(_key(passphrase, salt)).encrypt(
        iv,
        json.dumps(payload, separators=(",", ":")).encode(),
        None,
    )
    return {
        "version": 1,
        "algorithm": "AES-GCM",
        "kdf": "PBKDF2-SHA-256",
        "iterations": ITERATIONS,
        "salt": base64.b64encode(salt).decode(),
        "iv": base64.b64encode(iv).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
    }


def decrypt_packet(envelope: dict[str, Any], passphrase: str) -> dict[str, Any]:
    if (
        envelope.get("version") != 1
        or envelope.get("algorithm") != "AES-GCM"
        or envelope.get("kdf") != "PBKDF2-SHA-256"
        or envelope.get("iterations") != ITERATIONS
    ):
        raise ValueError("unsupported encrypted packet")
    try:
        plaintext = AESGCM(_key(passphrase, base64.b64decode(envelope["salt"], validate=True))).decrypt(
            base64.b64decode(envelope["iv"], validate=True),
            base64.b64decode(envelope["ciphertext"], validate=True),
            None,
        )
    except (InvalidTag, ValueError, KeyError) as exc:
        raise ValueError("packet authentication failed") from exc
    value = json.loads(plaintext)
    if not isinstance(value, dict):
        raise ValueError("decision packet must contain a JSON object")
    return value


def build_decision_packet(plan_id: str = "ACTIVE", database: str | Path | None = None) -> dict[str, Any]:
    plan = resolve_plan(plan_id, database)
    with session_scope(database) as session:
        quotes = session.scalars(select(QuoteRow).where(QuoteRow.plan_id == plan.id)).all()
        benchmarks = session.scalars(select(BenchmarkRow)).all()
        return {
            "schema_version": 1,
            "exported_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "vehicle_label": "2024 Honda CR-V Sport-L Hybrid AWD",
            "plan": {
                "id": plan.id,
                "service_codes": plan.service_codes.split(","),
                "odometer_miles": plan.odometer_miles,
            },
            "catalog": [rule.model_dump(mode="json") for rule in load_catalog().values()],
            "quotes": [
                {
                    "id": quote.id,
                    "shop_id": quote.shop_id,
                    "plan_id": quote.plan_id,
                    "received_at": quote.received_at.isoformat(),
                    "out_the_door_cents": quote.out_the_door_cents,
                    "warranty_score": quote.warranty_score,
                    "travel_minutes": quote.travel_minutes,
                    "completeness_score": quote.completeness_score,
                    "honda_hybrid_experience": quote.honda_hybrid_experience,
                    "comparable_scope": quote.comparable_scope,
                    "written": quote.written,
                }
                for quote in quotes
            ],
            "benchmarks": [
                {
                    "service_code": item.service_code,
                    "market": item.market,
                    "low_cents": item.low_cents,
                    "median_cents": item.median_cents,
                    "high_cents": item.high_cents,
                    "retrieved_at": item.retrieved_at.isoformat(),
                    "source_url": item.source_url,
                }
                for item in benchmarks
            ],
        }


def export_decision_packet(
    passphrase: str,
    *,
    plan_id: str = "ACTIVE",
    database: str | Path | None = None,
    output: str | Path | None = None,
) -> Path:
    payload = build_decision_packet(plan_id, database)
    envelope = encrypt_packet(payload, passphrase)
    target = Path(output) if output else data_paths().ensure().exports / f"{payload['plan']['id']}.encrypted.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    return target


def import_decision_packet(
    path: str | Path,
    passphrase: str,
    *,
    database: str | Path | None = None,
) -> dict[str, Any]:
    source = Path(path)
    payload = decrypt_packet(json.loads(source.read_text(encoding="utf-8")), passphrase)
    if payload.get("schema_version") != 1 or not isinstance(payload.get("plan"), dict):
        raise ValueError("unsupported decision packet schema")
    on_site = payload.get("on_site")
    if not isinstance(on_site, dict) or not isinstance(on_site.get("support_state"), str):
        raise ValueError("packet does not contain a reviewed on-site decision")
    record_id = f"decision-{uuid4().hex[:12]}"
    with session_scope(database) as session:
        session.add(
            DecisionPacketRow(
                id=record_id,
                plan_id=str(payload["plan"]["id"]),
                imported_at=datetime.now(),
                support_state=str(on_site["support_state"]),
                payload_json=json.dumps(payload, separators=(",", ":")),
            )
        )
    return {
        "decision_record_id": record_id,
        "plan_id": payload["plan"]["id"],
        "support_state": on_site["support_state"],
        "external_action_taken": False,
    }
