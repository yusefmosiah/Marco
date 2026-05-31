from __future__ import annotations

import hashlib
import json
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SourceRecord:
    logical_name: str
    url: str
    sha256: str
    bytes: int
    fetched_at: str
    raw_path: str


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download_bytes(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "emf/0.1 source-linked macro lab",
            "Accept": "text/csv,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read()


def cache_source(logical_name: str, url: str, raw_dir: Path) -> SourceRecord:
    ensure_dir(raw_dir)
    data = download_bytes(url)
    digest = sha256_bytes(data)
    suffix = ".csv" if ".csv" in url.lower() else ".bin"
    raw_path = raw_dir / f"{digest}{suffix}"
    if not raw_path.exists():
        raw_path.write_bytes(data)
    return SourceRecord(
        logical_name=logical_name,
        url=url,
        sha256=digest,
        bytes=len(data),
        fetched_at=datetime.now(UTC).isoformat(),
        raw_path=str(raw_path),
    )


def write_json(path: Path, payload: object) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    ensure_dir(path.parent)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def write_manifest(path: Path, records: Iterable[SourceRecord]) -> None:
    write_json(path, [asdict(record) for record in records])
