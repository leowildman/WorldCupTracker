from __future__ import annotations

import re
import unicodedata

from bs4 import BeautifulSoup

from worldcup_tracker.models import BookingStatus, Fixture
from worldcup_tracker.parsers.base import VenueParser

FIXTURE_LINE_RE = re.compile(
    r"^(?P<dow>\w{3})\s+(?P<day>\d{1,2})(?:\s+(?P<month>\w+))?"
    r"\s*-\s*(?P<time>\d{1,2}(?::\d{2})?\s*(?:am|pm))\s*-\s*(?P<teams>.+)$",
    re.IGNORECASE,
)
DEFAULT_MONTH = "Jun"


class BigPennyParser(VenueParser):
    """Parser for Big Penny Social World Cup fixture list (plain text in HTML)."""

    def parse(
        self,
        html: str,
        *,
        source_url: str | None = None,
        venue_name: str | None = None,
    ) -> list[Fixture]:
        soup = BeautifulSoup(html, "html.parser")
        fixture_paragraph = self._find_fixture_paragraph(soup)
        if fixture_paragraph is None:
            return []

        lines = self._split_fixture_lines(fixture_paragraph)
        fixtures: list[Fixture] = []
        for line in lines:
            parsed = self._parse_line(line)
            if parsed is None:
                continue
            date_label, time_label, teams = parsed
            fixture_slug = self._fixture_slug(date_label, time_label, teams)
            fixtures.append(
                Fixture(
                    teams=teams,
                    date_label=date_label,
                    time_label=time_label,
                    booking_status=BookingStatus.BOOKABLE,
                    booking_url=None,
                    fixture_slug=fixture_slug,
                    venue_name=venue_name,
                    source_url=source_url,
                )
            )
        return fixtures

    def _find_fixture_paragraph(self, soup: BeautifulSoup):
        for heading in soup.find_all("h2"):
            if "FIXTURES" not in heading.get_text(strip=True).upper():
                continue
            for paragraph in heading.find_all_next("p"):
                text = paragraph.get_text()
                if " v " in text or " vs " in text.lower():
                    return paragraph
        for paragraph in soup.find_all("p"):
            if "Mexico v South Africa" in paragraph.get_text():
                return paragraph
        return None

    def _split_fixture_lines(self, paragraph) -> list[str]:
        raw_html = str(paragraph)
        parts = re.split(r"<br\s*/?>", raw_html, flags=re.IGNORECASE)
        lines: list[str] = []
        for part in parts:
            text = BeautifulSoup(part, "html.parser").get_text(strip=True)
            if text:
                lines.append(text)
        return lines

    def _parse_line(self, line: str) -> tuple[str, str, str] | None:
        match = FIXTURE_LINE_RE.match(line.strip())
        if not match:
            return None

        month = match.group("month") or DEFAULT_MONTH
        date_label = f"{match.group('dow')} {match.group('day')} {month}"
        time_label = re.sub(r"\s+", "", match.group("time").lower())
        teams = self._normalize_teams(match.group("teams"))
        return date_label, time_label, teams

    def _normalize_teams(self, raw: str) -> str:
        teams = unicodedata.normalize("NFKC", raw.strip())
        teams = re.sub(r"\s+v\s+", " vs ", teams, flags=re.IGNORECASE)
        teams = re.sub(r"\s+", " ", teams)
        return teams

    def _fixture_slug(self, date_label: str, time_label: str, teams: str) -> str:
        slug_base = f"{date_label}-{time_label}-{teams}".lower()
        slug_base = unicodedata.normalize("NFKD", slug_base)
        slug_base = slug_base.encode("ascii", "ignore").decode("ascii")
        slug_base = re.sub(r"[^a-z0-9]+", "-", slug_base).strip("-")
        return f"big-penny/{slug_base}"
