from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CATALOG_SCHEMA = "marco.macro_sources.v1"


class MacroSourceCatalog:
    def __init__(self, root: Path):
        self.root = root
        self.catalog_path = root / "configs" / "macro_sources.json"

    def load(self) -> dict[str, Any]:
        payload = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        if payload.get("schema") != CATALOG_SCHEMA:
            raise ValueError(f"unsupported source catalog schema: {payload.get('schema')}")
        return payload

    def list(
        self,
        *,
        priority: str | None = None,
        status: str | None = None,
        region: str | None = None,
    ) -> list[dict[str, Any]]:
        sources = self.load()["sources"]
        rows = []
        for source in sources:
            if priority and source["priority"] != priority:
                continue
            if status and source["status"] != status:
                continue
            if region and region not in source["regions"]:
                continue
            rows.append(source)
        return sorted(rows, key=lambda row: (row["priority"], row["id"]))

    def inspect(self, source_id: str) -> dict[str, Any]:
        for source in self.load()["sources"]:
            if source["id"] == source_id:
                return source
        raise KeyError(source_id)
