from worldcup_tracker.models import BookingStatus, Fixture
from worldcup_tracker.sanity import suspicious_snapshot_regression


def _fixture(teams: str) -> Fixture:
    return Fixture(
        teams=teams,
        date_label="Thu 11 Jun",
        time_label="8pm",
        booking_status=BookingStatus.UNKNOWN,
        booking_url=None,
        fixture_slug=f"slug-{teams}",
    )


def test_sanity_allows_normal_changes() -> None:
    previous = [_fixture(f"Match {i}") for i in range(10)]
    current = previous + [_fixture("New Final")]
    assert suspicious_snapshot_regression(previous, current) is None


def test_sanity_blocks_empty_parse() -> None:
    previous = [_fixture(f"Match {i}") for i in range(5)]
    reason = suspicious_snapshot_regression(previous, [])
    assert reason is not None
    assert "0 fixtures" in reason


def test_sanity_blocks_sharp_drop() -> None:
    previous = [_fixture(f"Match {i}") for i in range(20)]
    current = previous[:5]
    reason = suspicious_snapshot_regression(previous, current)
    assert reason is not None
    assert "dropped sharply" in reason
