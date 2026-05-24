from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from worldcup_tracker.models import BookingStatus, Fixture
from worldcup_tracker.parsers.base import VenueParser

BASE_URL = "https://www.urbanpubsandbars.com"
WALK_INS_PATTERN = re.compile(r"walk\s*ins?\s*only", re.IGNORECASE)


class UrbanPubsParser(VenueParser):
    """Parser for Urban Pubs & Bars World Cup venue pages (Webflow CMS)."""

    def parse(
        self,
        html: str,
        *,
        source_url: str | None = None,
        venue_name: str | None = None,
    ) -> list[Fixture]:
        soup = BeautifulSoup(html, "html.parser")
        fixtures: list[Fixture] = []

        for item in soup.select("div.sport-item"):
            heading = item.select_one("h3.heading-fixture")
            if heading is None:
                continue

            teams = heading.get_text(strip=True)
            date_label, time_label = self._parse_datetime(item)
            fixture_slug = self._fixture_slug(item)
            booking_url = self._booking_url(item, source_url)
            booking_status = self._booking_status(item, booking_url)

            fixtures.append(
                Fixture(
                    teams=teams,
                    date_label=date_label,
                    time_label=time_label,
                    booking_status=booking_status,
                    booking_url=booking_url,
                    fixture_slug=fixture_slug,
                    venue_name=venue_name,
                    source_url=source_url,
                )
            )

        return fixtures

    def _parse_datetime(self, item) -> tuple[str, str]:
        wrapper = item.select_one("div.sport-date-wrapper")
        if wrapper is None:
            return "", ""

        parts = [
            el.get_text(strip=True)
            for el in wrapper.select("div.alt-text-medium")
            if el.get_text(strip=True) and el.get_text(strip=True) != "-"
        ]
        if len(parts) >= 4:
            # Thu, 11, Jun, 8:00 pm
            date_label = f"{parts[0]} {parts[1]} {parts[2]}"
            time_label = parts[3]
            return date_label, time_label
        if len(parts) == 3:
            return " ".join(parts[:2]), parts[2]
        if parts:
            return " ".join(parts[:-1]), parts[-1]
        return "", ""

    def _fixture_slug(self, item) -> str | None:
        link = item.select_one("a.nest-link")
        if link and link.get("href"):
            return link["href"].strip()
        return None

    def _booking_url(self, item, source_url: str | None) -> str | None:
        for anchor in item.select("a.button-sport"):
            href = (anchor.get("href") or "").strip()
            if href and href != "#":
                return urljoin(source_url or BASE_URL, href)
        return None

    def _booking_status(self, item, booking_url: str | None) -> BookingStatus:
        notification = item.select_one("div.notification-specific")
        notice_text = notification.get_text(" ", strip=True) if notification else ""

        if notice_text and WALK_INS_PATTERN.search(notice_text):
            return BookingStatus.WALK_INS_ONLY
        if booking_url:
            return BookingStatus.BOOKABLE
        book_buttons = item.select("a.button-sport")
        if book_buttons:
            return BookingStatus.WALK_INS_ONLY
        return BookingStatus.UNKNOWN
