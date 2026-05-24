from __future__ import annotations

import httpx

from worldcup_tracker.config import FetchSettings


def fetch_page(url: str, settings: FetchSettings) -> str:
    """Fetch a venue page HTML with a respectful user-agent and timeout."""
    headers = {"User-Agent": settings.user_agent, "Accept": "text/html"}
    with httpx.Client(
        timeout=settings.timeout_seconds,
        follow_redirects=True,
        headers=headers,
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text
