from __future__ import annotations

from pathlib import Path

import pytest

from worldcup_tracker.models import BookingStatus
from worldcup_tracker.parsers.big_penny import BigPennyParser

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BIG_PENNY_HTML = FIXTURES_DIR / "big_penny_sample.html"
BIG_PENNY_URL = "https://bigpennysocial.co.uk/whats-on/world-cup"


@pytest.fixture
def big_penny_html() -> str:
    return BIG_PENNY_HTML.read_text(encoding="utf-8")


def test_parse_all_fixtures(big_penny_html: str) -> None:
    parser = BigPennyParser()
    fixtures = parser.parse(
        big_penny_html,
        source_url=BIG_PENNY_URL,
        venue_name="Big Penny Social",
    )

    assert len(fixtures) == 31
    assert fixtures[0].teams == "Mexico vs South Africa"
    assert fixtures[0].date_label == "Thu 11 Jun"
    assert fixtures[0].time_label == "8pm"
    assert fixtures[0].booking_status == BookingStatus.BOOKABLE
    assert fixtures[0].fixture_slug.startswith("big-penny/")


def test_parse_missing_month_line(big_penny_html: str) -> None:
    parser = BigPennyParser()
    fixtures = parser.parse(big_penny_html)
    portugal = next(f for f in fixtures if f.teams == "Portugal vs DR Congo")
    assert portugal.date_label == "Wed 17 Jun"
    assert portugal.time_label == "6pm"


def test_parse_england_fixture(big_penny_html: str) -> None:
    parser = BigPennyParser()
    fixtures = parser.parse(big_penny_html)
    england = [f for f in fixtures if "England" in f.teams]
    assert len(england) == 3
    assert england[0].teams == "England vs Croatia"
