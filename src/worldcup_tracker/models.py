from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class BookingStatus(str, Enum):
    BOOKABLE = "bookable"
    WALK_INS_ONLY = "walk_ins_only"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Fixture:
    """A single match listing on a venue page."""

    teams: str
    date_label: str
    time_label: str
    booking_status: BookingStatus
    booking_url: str | None
    fixture_slug: str | None
    venue_name: str | None = None
    source_url: str | None = None

    @property
    def key(self) -> str:
        """Stable identifier for diffing across fetches."""
        slug = self.fixture_slug or ""
        if slug:
            return slug
        return f"{self.teams}|{self.date_label}|{self.time_label}"

    @property
    def display_datetime(self) -> str:
        return f"{self.date_label} {self.time_label}".strip()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["booking_status"] = self.booking_status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Fixture:
        status = data.get("booking_status", BookingStatus.UNKNOWN.value)
        if isinstance(status, BookingStatus):
            booking_status = status
        else:
            booking_status = BookingStatus(status)
        return cls(
            teams=data["teams"],
            date_label=data["date_label"],
            time_label=data["time_label"],
            booking_status=booking_status,
            booking_url=data.get("booking_url"),
            fixture_slug=data.get("fixture_slug"),
            venue_name=data.get("venue_name"),
            source_url=data.get("source_url"),
        )


@dataclass(frozen=True, slots=True)
class FixtureChange:
    kind: str
    fixture: Fixture
    previous: Fixture | None = None
    message: str = ""
