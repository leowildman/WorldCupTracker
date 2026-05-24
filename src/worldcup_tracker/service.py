from __future__ import annotations

from worldcup_tracker.config import AppConfig, VenueConfig
from worldcup_tracker.diff import compare_fixtures
from worldcup_tracker.fetcher import fetch_page
from worldcup_tracker.models import Fixture, FixtureChange
from worldcup_tracker.parsers import get_parser
from worldcup_tracker.storage import load_snapshot, save_snapshot


def fetch_venue_fixtures(
    venue: VenueConfig,
    config: AppConfig,
    *,
    html: str | None = None,
) -> list[Fixture]:
    page_html = html if html is not None else fetch_page(venue.url, config.fetch)
    parser = get_parser(venue.parser)
    return parser.parse(page_html, source_url=venue.url, venue_name=venue.name)


def check_venue(
    venue: VenueConfig,
    config: AppConfig,
    *,
    html: str | None = None,
    save: bool = True,
) -> tuple[list[Fixture], list[FixtureChange]]:
    previous = load_snapshot(config.data_dir, venue.name)
    current = fetch_venue_fixtures(venue, config, html=html)
    changes = compare_fixtures(previous, current)
    if save:
        save_snapshot(
            config.data_dir,
            venue.name,
            current,
            source_url=venue.url,
            archive=previous is not None,
        )
    return current, changes


def check_all(
    config: AppConfig,
    *,
    html_by_url: dict[str, str] | None = None,
    save: bool = True,
) -> dict[str, tuple[list[Fixture], list[FixtureChange]]]:
    results: dict[str, tuple[list[Fixture], list[FixtureChange]]] = {}
    for venue in config.venues:
        html = html_by_url.get(venue.url) if html_by_url else None
        results[venue.name] = check_venue(venue, config, html=html, save=save)
    return results
