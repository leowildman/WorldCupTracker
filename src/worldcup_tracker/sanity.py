"""Guard against false positives when a fetch or parse looks broken."""

from __future__ import annotations

from worldcup_tracker.models import Fixture


def suspicious_snapshot_regression(
    previous: list[Fixture],
    current: list[Fixture],
    *,
    min_previous: int = 3,
    min_retained_ratio: float = 0.5,
) -> str | None:
    """Return a human-readable reason to skip diff/save, or None if the fetch looks sane."""
    if not previous:
        return None

    prev_n = len(previous)
    curr_n = len(current)

    if curr_n == 0:
        return (
            f"parser returned 0 fixtures (previous snapshot had {prev_n}); "
            "likely a fetch or HTML change — snapshot not updated"
        )

    if prev_n >= min_previous and curr_n < prev_n * min_retained_ratio:
        return (
            f"fixture count dropped sharply ({prev_n} -> {curr_n}); "
            "likely a parse failure — snapshot not updated"
        )

    return None
