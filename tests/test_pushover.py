from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from worldcup_tracker.config import AppConfig, FetchSettings, NotificationSettings, VenueConfig
from worldcup_tracker.models import BookingStatus, Fixture, FixtureChange
from worldcup_tracker.pushover import (
    format_notification,
    notify_changes,
    resolve_pushover_credentials,
)


def _change(kind: str, message: str) -> FixtureChange:
    fixture = Fixture(
        teams="Brazil vs Argentina",
        date_label="Sun 28 Jun",
        time_label="3pm",
        booking_status=BookingStatus.BOOKABLE,
        booking_url=None,
        fixture_slug="big-penny/test",
    )
    return FixtureChange(kind=kind, fixture=fixture, message=message)


def test_format_notification_message() -> None:
    changes = {
        "Big Penny Social": [
            _change("new", "New fixture: Brazil vs Argentina (Sun 28 Jun 3pm)"),
        ],
    }
    title, message = format_notification(changes)
    assert title == "World Cup Tracker: 1 change"
    assert "Big Penny Social:" in message
    assert "Brazil vs Argentina" in message


def test_notify_skips_when_disabled() -> None:
    config = AppConfig(
        venues=[],
        fetch=FetchSettings(user_agent="test"),
        notifications=NotificationSettings(enabled=False),
        data_dir=Path("data"),
        config_path=Path("config.yaml"),
    )
    assert notify_changes(config, {"Venue": [_change("new", "New fixture: x")]}) is False


def test_notify_warns_without_credentials(caplog: pytest.LogCaptureFixture) -> None:
    config = AppConfig(
        venues=[],
        fetch=FetchSettings(user_agent="test"),
        notifications=NotificationSettings(enabled=True),
        data_dir=Path("data"),
        config_path=Path("config.yaml"),
    )
    with caplog.at_level("WARNING"):
        sent = notify_changes(config, {"Venue": [_change("new", "New fixture: x")]})
    assert sent is False
    assert "PUSHOVER_USER_KEY" in caplog.text


def test_notify_strict_raises_without_credentials() -> None:
    config = AppConfig(
        venues=[],
        fetch=FetchSettings(user_agent="test"),
        notifications=NotificationSettings(enabled=True, strict=True),
        data_dir=Path("data"),
        config_path=Path("config.yaml"),
    )
    with pytest.raises(RuntimeError, match="PUSHOVER_USER_KEY"):
        notify_changes(config, {"Venue": [_change("new", "New fixture: x")]})


@patch.dict(
    "os.environ",
    {"PUSHOVER_USER_KEY": "user123", "PUSHOVER_API_TOKEN": "token456"},
    clear=False,
)
def test_notify_sends_with_mocked_client() -> None:
    config = AppConfig(
        venues=[],
        fetch=FetchSettings(user_agent="test"),
        notifications=NotificationSettings(enabled=True, priority=1),
        data_dir=Path("data"),
        config_path=Path("config.yaml"),
    )
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_response

    changes = {"Bar Kick": [_change("new", "New fixture: Brazil vs Argentina")]}
    assert notify_changes(config, changes, client=mock_client) is True

    mock_client.post.assert_called_once()
    call_kwargs = mock_client.post.call_args
    assert call_kwargs[0][0] == "https://api.pushover.net/1/messages.json"
    payload = call_kwargs[1]["data"]
    assert payload["user"] == "user123"
    assert payload["token"] == "token456"
    assert payload["priority"] == 1
    assert "Brazil vs Argentina" in payload["message"]


def test_resolve_credentials_prefers_env() -> None:
    settings = NotificationSettings(
        user_key="config-user",
        api_token="config-token",
    )
    with patch.dict(
        "os.environ",
        {"PUSHOVER_USER_KEY": "env-user", "PUSHOVER_API_TOKEN": "env-token"},
    ):
        user, token = resolve_pushover_credentials(settings)
    assert user == "env-user"
    assert token == "env-token"
