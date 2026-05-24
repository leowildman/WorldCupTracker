from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import httpx

from worldcup_tracker.models import FixtureChange

if TYPE_CHECKING:
    from worldcup_tracker.config import AppConfig, NotificationSettings

logger = logging.getLogger(__name__)

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"


def resolve_pushover_credentials(
    settings: NotificationSettings,
) -> tuple[str | None, str | None]:
    user_key = os.environ.get("PUSHOVER_USER_KEY") or settings.user_key
    api_token = os.environ.get("PUSHOVER_API_TOKEN") or settings.api_token
    return user_key, api_token


def format_notification(changes_by_venue: dict[str, list[FixtureChange]]) -> tuple[str, str]:
    total = sum(len(changes) for changes in changes_by_venue.values())
    title = f"World Cup Tracker: {total} change{'s' if total != 1 else ''}"

    lines: list[str] = []
    for venue_name, changes in changes_by_venue.items():
        lines.append(f"{venue_name}:")
        for change in changes[:8]:
            lines.append(f"• {change.message}")
        if len(changes) > 8:
            lines.append(f"• …and {len(changes) - 8} more")
        lines.append("")

    message = "\n".join(lines).strip()
    if len(message) > 1024:
        message = message[:1020] + "…"
    return title, message


def send_pushover_message(
    *,
    user_key: str,
    api_token: str,
    title: str,
    message: str,
    priority: int = 0,
    client: httpx.Client | None = None,
) -> None:
    payload = {
        "user": user_key,
        "token": api_token,
        "title": title,
        "message": message,
        "priority": priority,
    }
    if client is not None:
        response = client.post(PUSHOVER_API_URL, data=payload)
    else:
        with httpx.Client(timeout=30.0) as http_client:
            response = http_client.post(PUSHOVER_API_URL, data=payload)
    response.raise_for_status()


def notify_changes(
    config: AppConfig,
    changes_by_venue: dict[str, list[FixtureChange]],
    *,
    client: httpx.Client | None = None,
) -> bool:
    """Send Pushover notification when changes exist. Returns True if sent."""
    if not changes_by_venue:
        return False

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

    title, message = format_notification(changes_by_venue)
    send_pushover_message(
        user_key=user_key,
        api_token=api_token,
        title=title,
        message=message,
        priority=settings.priority,
        client=client,
    )
    return True
