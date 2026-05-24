from __future__ import annotations

from dataclasses import dataclass

from worldcup_tracker.health import HealthAlert
from worldcup_tracker.models import Fixture, FixtureChange


@dataclass(frozen=True, slots=True)
class VenueCheckResult:
    fixtures: list[Fixture]
    changes: list[FixtureChange]
    skip_reason: str | None = None
    health_alert: HealthAlert | None = None
    health_recovered: bool = False
