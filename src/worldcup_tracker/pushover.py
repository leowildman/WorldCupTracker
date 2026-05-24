from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

from worldcup_tracker.health import HealthAlert
from worldcup_tracker.models import FixtureChange

if TYPE_CHECKING:
    from worldcup_tracker.config import AppConfig, NotificationSettings

logger = logging.getLogger(__name__)

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"

_KIND_LABELS = {
    "new": "new",
    "removed": "removed",
    "booking_changed": "booking",
    "booking_url_changed": "booking url",
    "details_changed": "details",
}


@dataclass(frozen=True, slots=True)
class PushoverMessage:
    title: str
    message: str
    url: str | None = None
    url_title: str | None = None


def resolve_pushover_credentials(
    settings: NotificationSettings,
) -> tuple[str | None, str | None]:
    user_key = os.environ.get("PUSHOVER_USER_KEY") or settings.user_key
    api_token = os.environ.get("PUSHOVER_API_TOKEN") or settings.api_token
    return user_key, api_token


def _change_line(change: FixtureChange) -> str:
    label = _KIND_LABELS.get(change.kind, change.kind)
    line = f"• [{label}] {change.message}"
    if change.fixture.booking_url:
        line += f"\n  {change.fixture.booking_url}"
    return line


def format_notification(
    changes_by_venue: dict[str, list[FixtureChange]],
    venue_urls: dict[str, str],
) -> PushoverMessage:
    total = sum(len(changes) for changes in changes_by_venue.values())
    title = f"World Cup Tracker: {total} change{'s' if total != 1 else ''}"

    lines: list[str] = []
    for venue_name, changes in changes_by_venue.items():
        lines.append(f"{venue_name}:")
        venue_url = venue_urls.get(venue_name) or next(
            (c.fixture.source_url for c in changes if c.fixture.source_url),
            None,
        )
        for change in changes[:8]:
            lines.append(_change_line(change))
        if len(changes) > 8:
            lines.append(f"• …and {len(changes) - 8} more")
        if venue_url:
            lines.append(f"Venue page: {venue_url}")
        lines.append("")

    message = "\n".join(lines).strip()
    if len(message) > 1024:
        message = message[:1020] + "…"

    url: str | None = None
    url_title: str | None = None
    if len(changes_by_venue) == 1:
        only_venue = next(iter(changes_by_venue))
        url = venue_urls.get(only_venue)
        if url:
            url_title = f"Open {only_venue}"

    return PushoverMessage(title=title, message=message, url=url, url_title=url_title)


def send_pushover_message(
    *,
    user_key: str,
    api_token: str,
    notification: PushoverMessage,
    priority: int = 0,
    client: httpx.Client | None = None,
) -> None:
    payload: dict[str, str | int] = {
        "user": user_key,
        "token": api_token,
        "title": notification.title,
        "message": notification.message,
        "priority": priority,
    }
    if notification.url:
        payload["url"] = notification.url
    if notification.url_title:
        payload["url_title"] = notification.url_title

    if client is not None:
        response = client.post(PUSHOVER_API_URL, data=payload)
    else:
        with httpx.Client(timeout=30.0) as http_client:
            response = http_client.post(PUSHOVER_API_URL, data=payload)
    response.raise_for_status()


def format_health_alert(alerts: list[HealthAlert]) -> PushoverMessage:
    if len(alerts) == 1:
        alert = alerts[0]
        title = "⚠️ Tracker: venue page broken"
        message = (
            f"{alert.venue_name} — {alert.consecutive_failures} failed checks in a row.\n\n"
            f"Last error: {alert.reason}\n\n"
            "The page may be down or the site layout changed. "
            "Snapshots were NOT updated.\n\n"
            f"Venue page: {alert.venue_url}"
        )
        return PushoverMessage(
            title=title,
            message=message,
            url=alert.venue_url,
            url_title=f"Open {alert.venue_name}",
        )

    title = f"⚠️ Tracker: {len(alerts)} venues broken"
    lines: list[str] = []
    for alert in alerts:
        lines.append(
            f"{alert.venue_name} ({alert.consecutive_failures} failures):\n"
            f"  {alert.reason}\n"
            f"  {alert.venue_url}\n"
        )
    return PushoverMessage(title=title, message="\n".join(lines).strip())


def format_health_recovery(venue_name: str, venue_url: str) -> PushoverMessage:
    return PushoverMessage(
        title="✅ Tracker: venue page OK again",
        message=(
            f"{venue_name} is responding normally again.\n\n"
            f"Venue page: {venue_url}"
        ),
        url=venue_url,
        url_title=f"Open {venue_name}",
    )


def _send_if_enabled(
    config: AppConfig,
    notification: PushoverMessage,
    *,
    priority: int,
    client: httpx.Client | None = None,
) -> bool:
    settings = config.notifications
    if not settings.enabled:
        return False

    user_key, api_token = resolve_pushover_credentials(settings)
    if not user_key or not api_token:
        msg = (
            "Pushover notifications enabled but PUSHOVER_USER_KEY "
            "and/or PUSHOVER_API_TOKEN are missing."
        )
        if settings.strict:
            raise RuntimeError(msg)
        logger.warning(msg)
        return False

    send_pushover_message(
        user_key=user_key,
        api_token=api_token,
        notification=notification,
        priority=priority,
        client=client,
    )
    return True


def notify_health_alerts(
    config: AppConfig,
    alerts: list[HealthAlert],
    *,
    client: httpx.Client | None = None,
) -> bool:
    """High-priority alert when a venue fails repeatedly."""
    if not alerts:
        return False
    notification = format_health_alert(alerts)
    return _send_if_enabled(
        config,
        notification,
        priority=config.notifications.health_priority,
        client=client,
    )


def notify_health_recovery(
    config: AppConfig,
    venue_name: str,
    venue_url: str,
    *,
    client: httpx.Client | None = None,
) -> bool:
    """Normal-priority notice when a venue recovers after a health alert."""
    notification = format_health_recovery(venue_name, venue_url)
    return _send_if_enabled(
        config,
        notification,
        priority=0,
        client=client,
    )


def notify_changes(
    config: AppConfig,
    changes_by_venue: dict[str, list[FixtureChange]],
    *,
    client: httpx.Client | None = None,
) -> bool:
    """Send Pushover notification when changes exist. Returns True if sent."""
    if not changes_by_venue:
        return False

    venue_urls = {v.name: v.url for v in config.venues}
    notification = format_notification(changes_by_venue, venue_urls)
    return _send_if_enabled(
        config,
        notification,
        priority=config.notifications.priority,
        client=client,
    )
