"""Verified copy of personal records into the external private store."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from .db import DocumentRow, session_scope
from .paths import DataPaths, data_paths
from .repository import seed_august_2026_event


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def migrate_records(
    source: str | Path,
    *,
    destination: str | Path | None = None,
    event_id: str = "service-2026-08-15",
) -> dict[str, object]:
    source_root = Path(source).resolve()
    if not source_root.is_dir():
        raise ValueError(f"source is not a directory: {source_root}")
    paths: DataPaths = data_paths(destination).ensure()
    target_root = paths.documents / "maintenance-records"
    copied: list[dict[str, object]] = []
    files = sorted(path for path in source_root.rglob("*") if path.is_file())
    if not files:
        raise ValueError("source directory contains no files")
    for source_path in files:
        rel = source_path.relative_to(source_root)
        target = target_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        source_hash = sha256_file(source_path)
        if target.exists() and sha256_file(target) != source_hash:
            raise ValueError(f"destination collision with different content: {target}")
        if not target.exists():
            shutil.copy2(source_path, target)
        target_hash = sha256_file(target)
        if target_hash != source_hash:
            raise OSError(f"checksum mismatch after copy: {source_path}")
        copied.append(
            {
                "relative_path": rel.as_posix(),
                "sha256": source_hash,
                "bytes": source_path.stat().st_size,
                "destination": str(target),
            }
        )
    event = seed_august_2026_event(paths.database)
    with session_scope(paths.database) as session:
        for item in copied:
            checksum = str(item["sha256"])
            existing = session.scalar(select(DocumentRow).where(DocumentRow.sha256 == checksum))
            if existing is None:
                session.add(
                    DocumentRow(
                        id=f"doc-{checksum[:16]}",
                        event_id=event_id,
                        original_name=Path(str(item["relative_path"])).name,
                        sha256=checksum,
                        local_path=str(item["destination"]),
                        reviewed=True,
                        extracted_text_path=None,
                    )
                )
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now().astimezone().isoformat(),
        "source": str(source_root),
        "destination": str(target_root),
        "file_count": len(copied),
        "total_bytes": sum(int(item["bytes"]) for item in copied),
        "source_left_untouched": True,
        "database": str(paths.database),
        "event": event,
        "files": copied,
    }
    manifest_path = paths.backups / f"import-manifest-{datetime.now():%Y%m%d-%H%M%S}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {**manifest, "manifest_path": str(manifest_path)}
