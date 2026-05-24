from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from worldcup_tracker.models import Fixture

_SNAPSHOT_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")


def _venue_dir(data_dir: Path, venue_name: str) -> Path:
    slug = _SNAPSHOT_SAFE.sub("_", venue_name.strip().lower())
    slug = slug.strip("_") or "venue"
    return data_dir / slug


def snapshot_path(data_dir: Path, venue_name: str) -> Path:
    return _venue_dir(data_dir, venue_name) / "latest.json"


def history_path(data_dir: Path, venue_name: str) -> Path:
    return _venue_dir(data_dir, venue_name) / "history"


def load_snapshot(data_dir: Path, venue_name: str) -> list[Fixture] | None:
    path = snapshot_path(data_dir, venue_name)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [Fixture.from_dict(item) for item in payload.get("fixtures", [])]


def save_snapshot(
    data_dir: Path,
    venue_name: str,
    fixtures: list[Fixture],
    *,
    source_url: str | None = None,
    archive: bool = True,
) -> Path:
    venue_path = _venue_dir(data_dir, venue_name)
    venue_path.mkdir(parents=True, exist_ok=True)

    latest = snapshot_path(data_dir, venue_name)
    if archive and latest.is_file():
        hist = history_path(data_dir, venue_name)
        hist.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        archived = hist / f"{stamp}.json"
        archived.write_text(latest.read_text(encoding="utf-8"), encoding="utf-8")

    payload = {
        "venue_name": venue_name,
        "source_url": source_url,
        "fetched_at": datetime.now(UTC).isoformat(),
        "fixtures": [f.to_dict() for f in fixtures],
    }
    latest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return latest
