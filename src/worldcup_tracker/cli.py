from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Annotated

import typer

from worldcup_tracker.config import load_config
from worldcup_tracker.env import load_env_file
from worldcup_tracker.diff import compare_fixtures
from worldcup_tracker.models import BookingStatus, FixtureChange
from worldcup_tracker.health import HealthAlert
from worldcup_tracker.pushover import (
    notify_changes,
    notify_health_alerts,
    notify_health_recovery,
)
from worldcup_tracker.service import check_all, check_venue, fetch_venue_fixtures
from worldcup_tracker.storage import load_snapshot

app = typer.Typer(
    name="worldcup-tracker",
    help="Monitor World Cup 2026 venue pages for new fixtures and booking changes.",
    no_args_is_help=True,
)


def _load(
    config: Path | None,
    data_dir: Path | None,
):
    load_env_file()
    return load_config(config_path=config, data_dir=data_dir)


def _status_label(status: BookingStatus) -> str:
    if status == BookingStatus.BOOKABLE:
        return "Bookable"
    if status == BookingStatus.WALK_INS_ONLY:
        return "Walk-ins only"
    return status.value


def _notify_pushover(
    cfg,
    changes_by_venue: dict[str, list[FixtureChange]],
    health_alerts: list[HealthAlert],
    recoveries: list[tuple[str, str]],
) -> None:
    try:
        if health_alerts and notify_health_alerts(cfg, health_alerts):
            typer.echo("Pushover health alert sent (high priority).")
        for venue_name, venue_url in recoveries:
            if notify_health_recovery(cfg, venue_name, venue_url):
                typer.echo(f"Pushover recovery notice sent for {venue_name}.")
        if changes_by_venue and notify_changes(cfg, changes_by_venue):
            typer.echo("Pushover notification sent.")
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


def _print_fixtures(fixtures, venue_name: str) -> None:
    typer.echo(f"\n{venue_name} ({len(fixtures)} fixtures)")
    typer.echo("-" * 60)
    for f in fixtures:
        status = _status_label(f.booking_status)
        typer.echo(f"  {f.teams}")
        typer.echo(f"    When: {f.display_datetime}")
        typer.echo(f"    Status: {status}")
        if f.booking_url:
            typer.echo(f"    Book: {f.booking_url}")


@app.command()
def check(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to config.yaml"),
    ] = None,
    data_dir: Annotated[
        Path | None,
        typer.Option("--data-dir", "-d", help="Directory for snapshots"),
    ] = None,
    venue: Annotated[
        str | None,
        typer.Option("--venue", "-v", help="Only check this venue name"),
    ] = None,
) -> None:
    """Fetch monitored venues, compare to last snapshot, and save state."""
    cfg = _load(config, data_dir)
    if not cfg.venues:
        typer.echo("No venues configured.", err=True)
        raise typer.Exit(1)

    any_changes = False
    changes_by_venue: dict[str, list[FixtureChange]] = {}
    health_alerts: list[HealthAlert] = []
    recoveries: list[tuple[str, str]] = []
    targets = [v for v in cfg.venues if venue is None or v.name == venue]
    if venue and not targets:
        typer.echo(f"Venue not found in config: {venue}", err=True)
        raise typer.Exit(1)

    for v in targets:
        result = check_venue(v, cfg)
        if result.health_alert:
            health_alerts.append(result.health_alert)
        if result.health_recovered:
            recoveries.append((v.name, v.url))
        if result.skip_reason:
            typer.echo(f"Warning for {v.name}: {result.skip_reason}", err=True)
            continue
        if result.changes:
            any_changes = True
            changes_by_venue[v.name] = result.changes
            typer.echo(f"\nChanges for {v.name}:")
            for change in result.changes:
                typer.echo(f"  [{change.kind}] {change.message}")
        else:
            typer.echo(
                f"No changes for {v.name} ({len(result.fixtures)} fixtures tracked)."
            )

    _notify_pushover(cfg, changes_by_venue, health_alerts, recoveries)
    raise typer.Exit(0 if not any_changes else 2)


@app.command("list")
def list_cmd(
    config: Annotated[Path | None, typer.Option("--config", "-c")] = None,
    data_dir: Annotated[Path | None, typer.Option("--data-dir", "-d")] = None,
    venue: Annotated[str | None, typer.Option("--venue", "-v")] = None,
    live: Annotated[
        bool,
        typer.Option("--live", help="Fetch live page instead of saved snapshot"),
    ] = False,
) -> None:
    """List fixtures from snapshots (default) or a live fetch."""
    cfg = _load(config, data_dir)
    targets = [v for v in cfg.venues if venue is None or v.name == venue]

    for v in targets:
        if live:
            fixtures = fetch_venue_fixtures(v, cfg)
        else:
            fixtures = load_snapshot(cfg.data_dir, v.name)
            if fixtures is None:
                typer.echo(f"No snapshot for {v.name}. Run `check` first.", err=True)
                continue
        _print_fixtures(fixtures, v.name)


@app.command()
def diff(
    config: Annotated[Path | None, typer.Option("--config", "-c")] = None,
    data_dir: Annotated[Path | None, typer.Option("--data-dir", "-d")] = None,
    venue: Annotated[str | None, typer.Option("--venue", "-v")] = None,
) -> None:
    """Show diff between saved snapshot and a fresh live fetch (does not save)."""
    cfg = _load(config, data_dir)
    targets = [v for v in cfg.venues if venue is None or v.name == venue]

    for v in targets:
        previous = load_snapshot(cfg.data_dir, v.name)
        current = fetch_venue_fixtures(v, cfg)
        changes = compare_fixtures(previous, current)
        typer.echo(f"\nDiff for {v.name} (snapshot vs live):")
        if not changes:
            typer.echo("  No differences.")
            continue
        for change in changes:
            typer.echo(f"  [{change.kind}] {change.message}")


@app.command()
def watch(
    interval: Annotated[
        int,
        typer.Option("--interval", "-i", help="Seconds between checks"),
    ] = 300,
    config: Annotated[Path | None, typer.Option("--config", "-c")] = None,
    data_dir: Annotated[Path | None, typer.Option("--data-dir", "-d")] = None,
) -> None:
    """Repeatedly run check at an interval until interrupted."""
    cfg = _load(config, data_dir)
    typer.echo(f"Watching {len(cfg.venues)} venue(s) every {interval}s (Ctrl+C to stop).")
    try:
        while True:
            results = check_all(cfg)
            changes_by_venue = {
                name: result.changes
                for name, result in results.items()
                if result.changes
            }
            health_alerts = [
                result.health_alert
                for result in results.values()
                if result.health_alert
            ]
            recoveries = [
                (name, next(v.url for v in cfg.venues if v.name == name))
                for name, result in results.items()
                if result.health_recovered
            ]
            for name, result in results.items():
                if result.skip_reason:
                    typer.echo(f"Warning for {name}: {result.skip_reason}", err=True)
            for name, changes in changes_by_venue.items():
                for change in changes:
                    typer.echo(f"[{name}] {change.message}")
            _notify_pushover(cfg, changes_by_venue, health_alerts, recoveries)
            time.sleep(interval)
    except KeyboardInterrupt:
        typer.echo("\nStopped.")
        raise typer.Exit(0) from None


def main() -> None:
    try:
        app()
    except typer.Exit as exc:
        sys.exit(exc.exit_code)


if __name__ == "__main__":
    main()
