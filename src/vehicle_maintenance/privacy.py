"""Fail-closed publication audit; gitignore is never treated as the boundary."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .models import PrivacyFinding, PrivacyReport

PRIVATE_ARTIFACT_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".heic", ".heif", ".pdf"}
MEDIA_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".heic", ".heif", ".pdf"}
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".mjs",
    ".html",
    ".css",
    ".csv",
}
SKIP_PARTS = {".git", ".venv", "node_modules", "dist", ".pytest_cache", ".ruff_cache"}
PRIVATE_ROOT_DIRECTORIES = {"documents", "ocr", "exports", "backups"}
PII_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "phone": re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)"),
    "vin": re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b"),
    "street_address": re.compile(
        r"\b\d{1,6}\s+[A-Z0-9][A-Z0-9 .'-]{2,40}\s"
        r"(?:ST|STREET|AVE|AVENUE|RD|ROAD|BLVD|DR|DRIVE|LN|LANE|CT|COURT|WAY)\b",
        re.IGNORECASE,
    ),
    "credential": re.compile(
        r"(?i)(?:(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_./+=-]{12,}['\"]"
        r"|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})"
    ),
}


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_synthetic_fixture(path: Path, root: Path) -> bool:
    parts = Path(_relative(path, root)).parts
    return len(parts) >= 3 and parts[:3] == ("tests", "fixtures", "synthetic")


def _is_generated_ocr_asset(path: Path, root: Path) -> bool:
    parts = Path(_relative(path, root)).parts
    return len(parts) >= 3 and parts[:3] == ("pwa", "public", "ocr")


def _gps_present(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            gps = exif.get_ifd(0x8825) if exif else {}
            return bool(gps)
    except (UnidentifiedImageError, OSError, KeyError, TypeError):
        return False


def audit_tree(root: str | Path) -> PrivacyReport:
    base = Path(root).resolve()
    findings: list[PrivacyFinding] = []
    scanned = 0
    for path in sorted(item for item in base.rglob("*") if item.is_file()):
        if any(part in SKIP_PARTS for part in path.relative_to(base).parts):
            continue
        scanned += 1
        rel = _relative(path, base)
        top_level = path.relative_to(base).parts[0]
        suffix = path.suffix.lower()
        if top_level in PRIVATE_ROOT_DIRECTORIES:
            findings.append(
                PrivacyFinding(
                    path=rel,
                    kind="private_store",
                    detail=f"private {top_level} directory is not allowed in source",
                )
            )
        if path.name == ".DS_Store":
            findings.append(PrivacyFinding(path=rel, kind="private_file", detail="Finder metadata file"))
        if path.name == ".env" or path.name.startswith(".env."):
            findings.append(PrivacyFinding(path=rel, kind="private_file", detail="environment file"))
        if ".local." in path.name:
            findings.append(PrivacyFinding(path=rel, kind="private_file", detail="local-only file in source tree"))
        if suffix in PRIVATE_ARTIFACT_SUFFIXES:
            if not (_is_synthetic_fixture(path, base) and suffix in MEDIA_SUFFIXES):
                findings.append(
                    PrivacyFinding(
                        path=rel,
                        kind="private_artifact",
                        detail=f"{suffix} is not allowed outside synthetic fixtures",
                    )
                )
        elif suffix in MEDIA_SUFFIXES and not _is_synthetic_fixture(path, base):
            findings.append(
                PrivacyFinding(
                    path=rel,
                    kind="media",
                    detail="media is not allowed outside tests/fixtures/synthetic",
                )
            )
        if suffix in MEDIA_SUFFIXES and _gps_present(path):
            findings.append(PrivacyFinding(path=rel, kind="exif_gps", detail="EXIF GPS metadata present"))
        if (
            (suffix in TEXT_SUFFIXES or path.name in {".env", ".mcp.json"})
            and path.name not in {"package-lock.json"}
            and not _is_generated_ocr_asset(path, base)
        ):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for kind, pattern in PII_PATTERNS.items():
                if pattern.search(text):
                    findings.append(PrivacyFinding(path=rel, kind=kind, detail=f"possible {kind}-like text"))
    return PrivacyReport(root=str(base), passed=not findings, scanned_files=scanned, findings=findings)
