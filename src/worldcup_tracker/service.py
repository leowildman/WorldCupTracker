from __future__ import annotations

import httpx

from worldcup_tracker.check_result import VenueCheckResult
from worldcup_tracker.config import AppConfig, VenueConfig
from worldcup_tracker.diff import compare_fixtures
from worldcup_tracker.fetcher import fetch_page
from worldcup_tracker.health import HealthAlert, record_failure, record_success
from worldcup_tracker.models import Fixture, FixtureChange
from worldcup_tracker.parsers import get_parser
from worldcup_tracker.sanity import suspicious_snapshot_regression
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


def _failure_settings(config: AppConfig) -> tuple[int, int]:
    n = config.notifications
    return n.health_alert_after, n.health_repeat_every


def _record_venue_failure(
    venue: VenueConfig,
    config: AppConfig,
    reason: str,
) -> HealthAlert | None:
    alert_after, repeat_every = _failure_settings(config)
    _, alert = record_failure(
        config.data_dir,
        venue.name,
        reason,
        alert_after=alert_after,
        repeat_every=repeat_every,
    )
    if alert is not None:
        return HealthAlert(
            venue_name=venue.name,
            venue_url=venue.url,
            consecutive_failures=alert.consecutive_failures,
            reason=reason,
        )
    return None


def check_venue(
    venue: VenueConfig,
    config: AppConfig,
    *,
    html: str | None = None,
    save: bool = True,
) -> VenueCheckResult:
    previous = load_snapshot(config.data_dir, venue.name)

    try:
        current = fetch_venue_fixtures(venue, config, html=html)
    except (httpx.HTTPError, OSError, ValueError) as exc:
        reason = f"Fetch failed: {exc}"
        health_alert = _record_venue_failure(venue, config, reason)
        fixtures = previous if previous is not None else []
        return VenueCheckResult(
            fixtures=fixtures,
            changes=[],
            skip_reason=reason,
            health_alert=health_alert,
        )

    skip_reason = None
    if previous is not None:
        skip_reason = suspicious_snapshot_regression(previous, current)

    if skip_reason:
        health_alert = _record_venue_failure(venue, config, skip_reason)
        return VenueCheckResult(
            fixtures=previous,
            changes=[],
            skip_reason=skip_reason,
            health_alert=health_alert,
        )

    health_recovered = record_success(config.data_dir, venue.name)
    changes = compare_fixtures(previous, current)
    if save:
        save_snapshot(
            config.data_dir,
            venue.name,
            current,
            source_url=venue.url,
            archive=previous is not None,
        )
    return VenueCheckResult(
        fixtures=current,
        changes=changes,
        health_recovered=health_recovered,
    )


def check_all(
    config: AppConfig,
    *,
    html_by_url: dict[str, str] | None = None,
    save: bool = True,
) -> dict[str, VenueCheckResult]:
    results: dict[str, VenueCheckResult] = {}
    for venue in config.venues:
        html = html_by_url.get(venue.url) if html_by_url else None
        results[venue.name] = check_venue(venue, config, html=html, save=save)
    return results
