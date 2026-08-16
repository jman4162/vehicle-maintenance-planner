"""Copyright-safe summarized Maintenance Minder catalog access."""

from __future__ import annotations

import json
import re
from importlib.resources import files

from .models import MaintenanceRule


def load_catalog() -> dict[str, MaintenanceRule]:
    resource = files("vehicle_maintenance.data").joinpath("catalog.us.2024-honda-crv-sport-l-hybrid-awd.json")
    raw = json.loads(resource.read_text(encoding="utf-8"))
    return {item["code"]: MaintenanceRule.model_validate(item) for item in raw["rules"]}


def expand_minder_code(displayed: str) -> list[str]:
    normalized = re.sub(r"[^A-Z0-9]", "", displayed.upper())
    codes: list[str] = []
    if normalized.startswith("A") or normalized.startswith("B"):
        codes.append(normalized[0])
        normalized = normalized[1:]
    codes.extend(char for char in normalized if char in "1234567")
    if not codes:
        raise ValueError(f"unrecognized Maintenance Minder code: {displayed!r}")
    return list(dict.fromkeys(codes))


def explain_minder_code(displayed: str) -> list[MaintenanceRule]:
    catalog = load_catalog()
    return [catalog[code] for code in expand_minder_code(displayed)]
