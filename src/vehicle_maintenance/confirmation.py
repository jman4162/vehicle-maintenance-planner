"""Payload-bound, expiring confirmation tokens for local MCP mutations."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .models import MutationPreview
from .paths import data_paths

TOKEN_LIFETIME_SECONDS = 300


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def _settings_secret(settings_path: Path | None = None) -> bytes:
    path = settings_path or data_paths().ensure().settings
    if path.exists():
        settings = json.loads(path.read_text(encoding="utf-8"))
    else:
        settings = {}
    if "confirmation_secret" not in settings:
        settings["confirmation_secret"] = secrets.token_hex(32)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return str(settings["confirmation_secret"]).encode()


def issue_preview(
    operation: str,
    payload: dict[str, Any],
    *,
    settings_path: Path | None = None,
    now: datetime | None = None,
) -> MutationPreview:
    current = now or datetime.now(UTC)
    expires = current + timedelta(seconds=TOKEN_LIFETIME_SECONDS)
    claims = {
        "operation": operation,
        "payload_sha256": hashlib.sha256(_canonical(payload)).hexdigest(),
        "expires_at": int(expires.timestamp()),
        "nonce": secrets.token_hex(8),
    }
    body = base64.urlsafe_b64encode(_canonical(claims)).rstrip(b"=")
    signature = hmac.new(_settings_secret(settings_path), body, hashlib.sha256).digest()
    token = f"{body.decode()}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"
    return MutationPreview(
        operation=operation,
        payload=payload,
        commit=False,
        confirmation_token=token,
        expires_at=expires,
    )


def validate_token(
    operation: str,
    payload: dict[str, Any],
    token: str,
    *,
    settings_path: Path | None = None,
    now: datetime | None = None,
) -> None:
    try:
        encoded, encoded_signature = token.split(".", 1)
        signature = base64.urlsafe_b64decode(encoded_signature + "=" * (-len(encoded_signature) % 4))
        expected = hmac.new(_settings_secret(settings_path), encoded.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("confirmation token signature is invalid")
        body = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        claims = json.loads(body)
    except (ValueError, json.JSONDecodeError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("confirmation"):
            raise
        raise ValueError("confirmation token is malformed") from exc
    if claims["operation"] != operation:
        raise ValueError("confirmation token is bound to a different operation")
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    if not hmac.compare_digest(claims["payload_sha256"], digest):
        raise ValueError("confirmation token is bound to a different payload")
    current = now or datetime.now(UTC)
    if current.timestamp() > int(claims["expires_at"]):
        raise ValueError("confirmation token has expired")
