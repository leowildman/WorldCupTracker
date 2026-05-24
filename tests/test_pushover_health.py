from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx

from worldcup_tracker.config import AppConfig, FetchSettings, NotificationSettings
from worldcup_tracker.health import HealthAlert
from worldcup_tracker.pushover import format_health_alert, notify_health_alerts


def test_format_health_alert_single() -> None:
    alert = HealthAlert(
        venue_name="Bar Kick",
        venue_url="https://example.com/venue",
        consecutive_failures=5,
        reason="parser returned 0 fixtures",
    )
    notification = format_health_alert([alert])
    assert "broken" in notification.title
    assert "5 failed checks" in notification.message
    assert notification.url == "https://example.com/venue"


@patch.dict(
    "os.environ",
    {"PUSHOVER_USER_KEY": "user123", "PUSHOVER_API_TOKEN": "token456"},
    clear=False,
)
def test_notify_health_uses_high_priority() -> None:
    config = AppConfig(
        venues=[],
        fetch=FetchSettings(user_agent="test"),
        notifications=NotificationSettings(enabled=True, health_priority=1),
        data_dir=Path("data"),
        config_path=Path("config.yaml"),
    )
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_response

    alerts = [
        HealthAlert(
            venue_name="Bar Kick",
            venue_url="https://example.com",
            consecutive_failures=5,
            reason="parse failure",
        )
    ]
    assert notify_health_alerts(config, alerts, client=mock_client) is True

    payload = mock_client.post.call_args[1]["data"]
    assert payload["priority"] == 1
    assert "broken" in payload["title"].lower() or "⚠" in payload["title"]
