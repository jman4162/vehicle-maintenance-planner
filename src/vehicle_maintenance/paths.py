"""Private data locations; no real vehicle data belongs in the package tree."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_data_path


@dataclass(frozen=True)
class DataPaths:
    root: Path
    database: Path
    documents: Path
    ocr: Path
    exports: Path
    backups: Path
    settings: Path

    def ensure(self) -> DataPaths:
        self.root.mkdir(parents=True, exist_ok=True)
        for directory in (self.documents, self.ocr, self.exports, self.backups):
            directory.mkdir(parents=True, exist_ok=True)
        return self


def data_paths(override: str | Path | None = None) -> DataPaths:
    configured = override or os.environ.get("VEHICLE_MAINT_DATA_DIR")
    root = (
        Path(configured).expanduser().resolve()
        if configured
        else Path(user_data_path("Vehicle Maintenance Planner", appauthor=False))
    )
    return DataPaths(
        root=root,
        database=root / "maintenance.sqlite3",
        documents=root / "documents",
        ocr=root / "ocr",
        exports=root / "exports",
        backups=root / "backups",
        settings=root / "settings.json",
    )
