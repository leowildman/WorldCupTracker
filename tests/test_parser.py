from __future__ import annotations

from worldcup_tracker.models import BookingStatus
from worldcup_tracker.parsers.urban_pubs import UrbanPubsParser

EXPECTED_TEAMS = [
    "Mexico vs South Africa",
    "Canada vs Bosnia",
    "Qatar vs Switzerland",
    "Germany vs Curacao",
    "Netherlands vs Japan",
    "Spain vs Cape Verde Islands",
    "Belgium vs Egypt",
    "France vs Senegal",
    "Portugal vs DR Congo",
    "England vs Croatia",
    "Czech Republic vs South Africa",
    "Switzerland vs Bosnia",
    "USA vs Australia",
    "Netherlands vs Sweden",
    "Germany vs Ivory Coast",
    "Spain vs Saudi Arabia",
    "Belgium vs Iran",
    "Argentina vs Austria",
    "France vs Iraq",
    "Portugal vs Uzbekistan",
    "England vs Ghana",
    "Bosnia vs Qatar",
    "Switzerland vs Canada",
    "Curacao vs Ivory Coast",
    "Ecuador vs Germany",
    "Norway vs France",
    "Senegal vs Iraq",
    "Croatia vs Ghana",
    "Panama vs England",
]


def test_parse_all_fixtures_from_sample(sample_html: str, bar_kick_url: str) -> None:
    parser = UrbanPubsParser()
    fixtures = parser.parse(
        sample_html,
        source_url=bar_kick_url,
        venue_name="Bar Kick at The Shoreditch Arms",
    )

    assert len(fixtures) == 29
    teams = [f.teams for f in fixtures]
    assert teams == EXPECTED_TEAMS


def test_parse_first_fixture_details(sample_html: str, bar_kick_url: str) -> None:
    parser = UrbanPubsParser()
    first = parser.parse(sample_html, source_url=bar_kick_url)[0]

    assert first.teams == "Mexico vs South Africa"
    assert first.date_label == "Thu 11 Jun"
    assert first.time_label == "8:00 pm"
    assert first.booking_status == BookingStatus.WALK_INS_ONLY
    assert first.booking_url is None
    assert first.fixture_slug == (
        "/world-cup-fixtures/fifa-world-cup-mexico-vs-south-africa-735743"
    )


def test_parse_bookable_fixture_from_modified_html(sample_html: str) -> None:
    modified = sample_html.replace(
        "Walk ins only for this match",
        "Tables available — book ahead",
        1,
    ).replace(
        'href="#" class="button-sport hide-on-load"',
        'href="https://booking.example.com/mexico-sa" class="button-sport hide-on-load"',
        1,
    )
    parser = UrbanPubsParser()
    first = parser.parse(modified)[0]

    assert first.booking_status == BookingStatus.BOOKABLE
    assert first.booking_url == "https://booking.example.com/mexico-sa"
