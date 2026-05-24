from __future__ import annotations

from worldcup_tracker.diff import compare_fixtures
from worldcup_tracker.models import BookingStatus, Fixture
from worldcup_tracker.parsers.urban_pubs import UrbanPubsParser


def _fixture(
    teams: str,
    *,
    status: BookingStatus = BookingStatus.WALK_INS_ONLY,
    slug: str | None = None,
) -> Fixture:
    return Fixture(
        teams=teams,
        date_label="Thu 11 Jun",
        time_label="8:00 pm",
        booking_status=status,
        booking_url=None,
        fixture_slug=slug or f"/fixture/{teams.lower().replace(' ', '-')}",
    )


def test_new_fixture_detected() -> None:
    previous = [_fixture("Mexico vs South Africa")]
    current = previous + [_fixture("Brazil vs Argentina", slug="/fixture/brazil-argentina")]

    changes = compare_fixtures(previous, current)
    assert len(changes) == 1
    assert changes[0].kind == "new"
    assert changes[0].fixture.teams == "Brazil vs Argentina"


def test_booking_status_change_detected() -> None:
    slug = "/world-cup-fixtures/fifa-world-cup-mexico-vs-south-africa-735743"
    previous = [_fixture("Mexico vs South Africa", slug=slug)]
    current = [
        Fixture(
            teams="Mexico vs South Africa",
            date_label="Thu 11 Jun",
            time_label="8:00 pm",
            booking_status=BookingStatus.BOOKABLE,
            booking_url="https://booking.example.com/mexico-sa",
            fixture_slug=slug,
        )
    ]

    changes = compare_fixtures(previous, current)
    assert len(changes) == 1
    assert changes[0].kind == "booking_changed"
    assert "walk_ins_only -> bookable" in changes[0].message


def test_integration_diff_from_modified_html(sample_html: str) -> None:
    parser = UrbanPubsParser()
    previous = parser.parse(sample_html)

    modified = sample_html + (
        '<div role="listitem" class="sport-item w-dyn-item">'
        '<div class="hide"><a href="/world-cup-fixtures/fifa-world-cup-brazil-vs-argentina-999999" '
        'class="nest-link"></a></div>'
        '<div class="sport-card-wrapper"><div class="sport-content-wrapper">'
        '<div class="sport-content"><h3 class="heading-fixture">Brazil vs Argentina</h3>'
        '<div class="sport-date-wrapper">'
        '<div class="alt-text-medium">Sun</div><div class="alt-text-medium">28</div>'
        '<div class="alt-text-medium">Jun</div><div class="alt-text-medium">-</div>'
        '<div class="alt-text-medium">3:00 pm</div></div>'
        '<a href="https://booking.example.com/brazil-argentina" class="button-sport">Book Now</a>'
        "</div></div></div></div>"
    )
    current = parser.parse(modified)
    changes = compare_fixtures(previous, current)

    kinds = {c.kind for c in changes}
    assert "new" in kinds
    new_teams = {c.fixture.teams for c in changes if c.kind == "new"}
    assert "Brazil vs Argentina" in new_teams
