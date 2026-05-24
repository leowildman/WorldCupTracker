"""Track consecutive fetch/parse failures per venue."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from worldcup_tracker.storage import _venue_dir


@dataclass(frozen=True, slots=True)
class VenueHealthState:
    consecutive_failures: int = 0
    last_failure_reason: str | None = None
    health_alert_sent: bool = False
    last_failure_at: str | None = None


@dataclass(frozen=True, slots=True)
class HealthAlert:
    venue_name: str
    venue_url: str
    consecutive_failures: int
    reason: str


def _health_path(data_dir: Path, venue_name: str) -> Path:
    return _venue_dir(data_dir, venue_name) / "health.json"


def load_health(data_dir: Path, venue_name: str) -> VenueHealthState:
    path = _health_path(data_dir, venue_name)
    if not path.is_file():
        return VenueHealthState()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return VenueHealthState(
        consecutive_failures=int(raw.get("consecutive_failures", 0)),
        last_failure_reason=raw.get("last_failure_reason"),
        health_alert_sent=bool(raw.get("health_alert_sent", False)),
        last_failure_at=raw.get("last_failure_at"),
    )


def save_health(data_dir: Path, venue_name: str, state: VenueHealthState) -> None:
    path = _health_path(data_dir, venue_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "consecutive_failures": state.consecutive_failures,
        "last_failure_reason": state.last_failure_reason,
        "health_alert_sent": state.health_alert_sent,
        "last_failure_at": state.last_failure_at,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def record_failure(
    data_dir: Path,
    venue_name: str,
    reason: str,
    *,
    alert_after: int = 5,
    repeat_every: int = 0,
) -> tuple[VenueHealthState, HealthAlert | None]:
    """Increment failure count; return a health alert when the threshold is reached."""
    state = load_health(data_dir, venue_name)
    count = state.consecutive_failures + 1
    now = datetime.now(UTC).isoformat()

    should_alert = False
    if count >= alert_after:
        if not state.health_alert_sent:
            should_alert = True
        elif repeat_every > 0 and count % repeat_every == 0:
            should_alert = True

    new_state = VenueHealthState(
        consecutive_failures=count,
        last_failure_reason=reason,
        health_alert_sent=state.health_alert_sent or should_alert,
        last_failure_at=now,
    )
    save_health(data_dir, venue_name, new_state)

    alert = None
    if should_alert:
        alert = HealthAlert(
            venue_name=venue_name,
            venue_url="",
            consecutive_failures=count,
            reason=reason,
        )
    return new_state, alert


def record_success(data_dir: Path, venue_name: str) -> bool:
    """Reset failure count. Returns True if the venue had an active health alert."""
    state = load_health(data_dir, venue_name)
    was_alerting = state.health_alert_sent and state.consecutive_failures > 0
    save_health(data_dir, venue_name, VenueHealthState())
    return was_alerting
