from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_NAME = "config.yaml"
DEFAULT_DATA_DIR = "data"


@dataclass(frozen=True, slots=True)
class FetchSettings:
    user_agent: str
    timeout_seconds: float = 30.0


@dataclass(frozen=True, slots=True)
class NotificationSettings:
    enabled: bool = False
    priority: int = 0
    strict: bool = False
    user_key: str | None = None
    api_token: str | None = None
    health_alert_after: int = 5
    health_priority: int = 1
    health_repeat_every: int = 0


@dataclass(frozen=True, slots=True)
class VenueConfig:
    name: str
    url: str
    parser: str = "urban_pubs"


@dataclass(frozen=True, slots=True)
class AppConfig:
    venues: list[VenueConfig]
    fetch: FetchSettings
    notifications: NotificationSettings
    data_dir: Path
    config_path: Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_config_path(config_path: str | Path | None = None) -> Path:
    if config_path is not None:
        return Path(config_path).expanduser().resolve()
    env_path = os.environ.get("WCT_CONFIG")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return _project_root() / DEFAULT_CONFIG_NAME


def resolve_data_dir(data_dir: str | Path | None = None) -> Path:
    if data_dir is not None:
        return Path(data_dir).expanduser().resolve()
    env_dir = os.environ.get("WCT_DATA_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return _project_root() / DEFAULT_DATA_DIR


def load_config(
    config_path: str | Path | None = None,
    data_dir: str | Path | None = None,
) -> AppConfig:
    path = resolve_config_path(config_path)
    raw: dict[str, Any] = {}
    if path.is_file():
        with path.open(encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

    fetch_raw = raw.get("fetch", {})
    user_agent = os.environ.get(
        "WCT_USER_AGENT",
        fetch_raw.get(
            "user_agent",
            "WorldCupTracker/0.1 (fixture monitor)",
        ),
    )
    timeout = float(
        os.environ.get(
            "WCT_HTTP_TIMEOUT",
            fetch_raw.get("timeout_seconds", 30),
        )
    )
    fetch = FetchSettings(user_agent=user_agent, timeout_seconds=timeout)

    notif_raw = raw.get("notifications", {})
    notifications = NotificationSettings(
        enabled=bool(notif_raw.get("enabled", False)),
        priority=int(notif_raw.get("priority", 0)),
        strict=bool(notif_raw.get("strict", False)),
        user_key=notif_raw.get("user_key"),
        api_token=notif_raw.get("api_token"),
        health_alert_after=int(notif_raw.get("health_alert_after", 5)),
        health_priority=int(notif_raw.get("health_priority", 1)),
        health_repeat_every=int(notif_raw.get("health_repeat_every", 0)),
    )

    venues: list[VenueConfig] = []
    for entry in raw.get("venues", []):
        venues.append(
            VenueConfig(
                name=entry["name"],
                url=entry["url"],
                parser=entry.get("parser", "urban_pubs"),
            )
        )

    return AppConfig(
        venues=venues,
        fetch=fetch,
        notifications=notifications,
        data_dir=resolve_data_dir(data_dir),
        config_path=path,
    )
