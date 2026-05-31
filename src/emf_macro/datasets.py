from __future__ import annotations

import csv
import hashlib
import json
import shutil
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatasetRecord:
    dataset_id: str
    name: str
    kind: str
    source_type: str
    source_uri: str
    stored_path: str
    sha256: str
    byte_size: int
    created_at: str
    format: str
    schema: dict[str, Any]
    tags: list[str]


@dataclass(frozen=True)
class DatasetMappingSpec:
    schema_version: str
    mapping_id: str
    dataset_id: str
    date_column: str
    value_columns: list[str]
    frequency: str
    country: str | None
    indicators: dict[str, str]
    units: dict[str, str]
    transformations: dict[str, str]
    vintage_policy: str
    source_snapshot_id: str | None = None


class DatasetRegistry:
    def __init__(self, root: Path):
        self.root = root
        self.registry_dir = root / "data" / "registry"
        self.upload_dir = root / "data" / "uploads"
        self.registry_path = self.registry_dir / "datasets.jsonl"

    def list(self) -> list[dict[str, Any]]:
        if not self.registry_path.exists():
            return []
        rows = []
        for line in self.registry_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return sorted(rows, key=lambda row: row["created_at"])

    def add_file(
        self,
        path: Path,
        *,
        name: str | None = None,
        kind: str = "time_series",
        source_type: str = "upload",
        source_uri: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(path)
        digest = sha256_file(path)
        dataset_id = dataset_id_for(name or path.stem, digest)
        target_dir = self.upload_dir / dataset_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / path.name
        if path.resolve() != target.resolve():
            shutil.copyfile(path, target)
        record = DatasetRecord(
            dataset_id=dataset_id,
            name=name or path.stem,
            kind=kind,
            source_type=source_type,
            source_uri=source_uri or str(path),
            stored_path=str(target.relative_to(self.root)),
            sha256=digest,
            byte_size=path.stat().st_size,
            created_at=utc_now(),
            format=path.suffix.lower().lstrip(".") or "unknown",
            schema=infer_schema(path),
            tags=tags or [],
        )
        return self._upsert(record)

    def fetch_url(
        self,
        url: str,
        *,
        name: str | None = None,
        kind: str = "time_series",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        filename = Path(urllib.parse.urlparse(url).path).name
        if not filename:
            filename = "dataset"
        tmp_dir = self.root / "tmp" / "dataset-fetch"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / filename
        with urllib.request.urlopen(url, timeout=30) as response:
            tmp_path.write_bytes(response.read())
        return self.add_file(tmp_path, name=name or Path(filename).stem, kind=kind, source_type="url", source_uri=url, tags=tags)

    def _upsert(self, record: DatasetRecord) -> dict[str, Any]:
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        rows = [row for row in self.list() if row["dataset_id"] != record.dataset_id]
        rows.append(asdict(record))
        self.registry_path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in sorted(rows, key=lambda row: row["created_at"])),
            encoding="utf-8",
        )
        return asdict(record)


def build_dataset_mapping_spec(
    record: dict[str, Any],
    *,
    date_column: str,
    value_columns: list[str],
    frequency: str,
    country: str | None = None,
    indicators: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    transformations: dict[str, str] | None = None,
    vintage_policy: str = "latest_revised_snapshot",
    source_snapshot_id: str | None = None,
) -> dict[str, Any]:
    spec = DatasetMappingSpec(
        schema_version="marco.dataset_mapping.v1",
        mapping_id=dataset_mapping_id(record["dataset_id"], date_column, value_columns, frequency, vintage_policy),
        dataset_id=record["dataset_id"],
        date_column=date_column,
        value_columns=value_columns,
        frequency=frequency,
        country=country,
        indicators=indicators or {},
        units=units or {},
        transformations=transformations or {},
        vintage_policy=vintage_policy,
        source_snapshot_id=source_snapshot_id,
    )
    payload = asdict(spec)
    validate_dataset_mapping_spec(record, payload)
    return payload


def validate_dataset_mapping_spec(record: dict[str, Any], spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != "marco.dataset_mapping.v1":
        raise ValueError("unsupported dataset mapping schema")
    if spec.get("dataset_id") != record.get("dataset_id"):
        raise ValueError("mapping dataset_id does not match dataset record")
    if spec.get("frequency") not in {"D", "W", "M", "Q", "A"}:
        raise ValueError("frequency must be one of D, W, M, Q, A")
    if spec.get("vintage_policy") not in {"latest_revised_snapshot", "real_time_vintage", "mixed"}:
        raise ValueError("unsupported vintage_policy")

    columns = set(record.get("schema", {}).get("columns", []))
    required_columns = [spec.get("date_column"), *spec.get("value_columns", [])]
    missing = sorted(column for column in required_columns if column not in columns)
    if missing:
        raise ValueError(f"mapping references missing columns: {', '.join(missing)}")


def dataset_mapping_id(dataset_id: str, date_column: str, value_columns: list[str], frequency: str, vintage_policy: str) -> str:
    payload = json.dumps(
        {
            "dataset_id": dataset_id,
            "date_column": date_column,
            "frequency": frequency,
            "value_columns": sorted(value_columns),
            "vintage_policy": vintage_policy,
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"map-{digest[:16]}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dataset_id_for(name: str, digest: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in name).strip("-")
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return f"{cleaned or 'dataset'}-{digest[:12]}"


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def infer_schema(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            header = next(reader, [])
            sample_rows = [row for _, row in zip(range(5), reader)]
        return {
            "columns": header,
            "sample_row_count": len(sample_rows),
            "column_count": len(header),
        }
    return {"columns": [], "sample_row_count": 0, "column_count": 0}
