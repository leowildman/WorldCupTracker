from pathlib import Path

from worldcup_tracker.config import AppConfig, FetchSettings, NotificationSettings, VenueConfig
from worldcup_tracker.models import BookingStatus, Fixture
from worldcup_tracker.service import check_venue
from worldcup_tracker.storage import save_snapshot


def _fixture(teams: str, slug: str) -> Fixture:
    return Fixture(
        teams=teams,
        date_label="Thu 11 Jun",
        time_label="8pm",
        booking_status=BookingStatus.UNKNOWN,
        booking_url=None,
        fixture_slug=slug,
    )


def test_check_venue_health_alert_after_threshold(tmp_path: Path) -> None:
    venue = VenueConfig(name="Test Venue", url="https://example.com", parser="urban_pubs")
    cfg = AppConfig(
        venues=[venue],
        fetch=FetchSettings(user_agent="test"),
        notifications=NotificationSettings(health_alert_after=3),
        data_dir=tmp_path,
        config_path=Path("config.yaml"),
    )
    previous = [_fixture(f"Match {i}", f"slug-{i}") for i in range(10)]
    save_snapshot(tmp_path, venue.name, previous, source_url=venue.url)
    empty_html = "<html><body></body></html>"

    alert = None
    for _ in range(3):
        result = check_venue(venue, cfg, html=empty_html, save=True)
        alert = result.health_alert

    assert alert is not None
    assert alert.consecutive_failures == 3


def test_check_venue_skips_save_on_suspicious_drop(tmp_path: Path) -> None:
    venue = VenueConfig(name="Test Venue", url="https://example.com", parser="urban_pubs")
    cfg = AppConfig(
        venues=[venue],
        fetch=FetchSettings(user_agent="test"),
        notifications=NotificationSettings(),
        data_dir=tmp_path,
        config_path=Path("config.yaml"),
    )
    previous = [_fixture(f"Match {i}", f"slug-{i}") for i in range(10)]
    save_snapshot(tmp_path, venue.name, previous, source_url=venue.url)

    empty_html = "<html><body><div>No fixtures</div></body></html>"
    result = check_venue(venue, cfg, html=empty_html, save=True)

    assert result.skip_reason is not None
    assert result.changes == []
    assert len(result.fixtures) == 10
    assert result.health_alert is None
