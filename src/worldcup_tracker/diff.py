from __future__ import annotations

from worldcup_tracker.models import BookingStatus, Fixture, FixtureChange


def compare_fixtures(
    previous: list[Fixture] | None,
    current: list[Fixture],
) -> list[FixtureChange]:
    """Detect new fixtures and booking-status changes."""
    if not previous:
        return [
            FixtureChange(kind="new", fixture=f, message=f"New fixture: {f.teams}")
            for f in current
        ]

    prev_by_key = {f.key: f for f in previous}
    changes: list[FixtureChange] = []

    for fixture in current:
        old = prev_by_key.get(fixture.key)
        if old is None:
            changes.append(
                FixtureChange(
                    kind="new",
                    fixture=fixture,
                    message=f"New fixture: {fixture.teams} ({fixture.display_datetime})",
                )
            )
            continue

        if old.booking_status != fixture.booking_status:
            changes.append(
                FixtureChange(
                    kind="booking_changed",
                    fixture=fixture,
                    previous=old,
                    message=(
                        f"Booking changed for {fixture.teams}: "
                        f"{old.booking_status.value} -> {fixture.booking_status.value}"
                    ),
                )
            )
        elif (
            old.booking_status == BookingStatus.BOOKABLE
            and fixture.booking_status == BookingStatus.BOOKABLE
            and old.booking_url != fixture.booking_url
            and fixture.booking_url
        ):
            changes.append(
                FixtureChange(
                    kind="booking_url_changed",
                    fixture=fixture,
                    previous=old,
                    message=f"Booking URL updated for {fixture.teams}",
                )
            )

    curr_by_key = {f.key: f for f in current}
    for old in previous:
        if old.key not in curr_by_key:
            changes.append(
                FixtureChange(
                    kind="removed",
                    fixture=old,
                    previous=old,
                    message=f"Removed fixture: {old.teams} ({old.display_datetime})",
                )
            )

    return changes
