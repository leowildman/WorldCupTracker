from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from worldcup_tracker.cli import app
from worldcup_tracker.config import load_config
from worldcup_tracker.service import check_venue
from worldcup_tracker.storage import load_snapshot

runner = CliRunner()

NEW_FIXTURE_HTML = (
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


def test_check_cli_with_fixture_html(
    temp_config: Path,
    temp_data_dir: Path,
    sample_html: str,
) -> None:
    cfg = load_config(temp_config, temp_data_dir)
    venue = cfg.venues[0]

    check_venue(venue, cfg, html=sample_html, save=True)
    assert load_snapshot(temp_data_dir, venue.name) is not None

    current_html = {"value": sample_html}

    def fake_fetch_page(url: str, settings) -> str:
        return current_html["value"]

    with patch("worldcup_tracker.service.fetch_page", side_effect=fake_fetch_page):
        result = runner.invoke(
            app,
            ["check", "-c", str(temp_config), "-d", str(temp_data_dir)],
        )
        assert result.exit_code == 0
        assert "No changes" in result.stdout

        current_html["value"] = sample_html + NEW_FIXTURE_HTML
        result = runner.invoke(
            app,
            ["check", "-c", str(temp_config), "-d", str(temp_data_dir)],
        )

    assert result.exit_code == 2
    assert "New fixture" in result.stdout
    assert "Brazil vs Argentina" in result.stdout


def test_list_cli_after_check(
    temp_config: Path,
    temp_data_dir: Path,
    sample_html: str,
) -> None:
    cfg = load_config(temp_config, temp_data_dir)
    check_venue(cfg.venues[0], cfg, html=sample_html, save=True)

    result = runner.invoke(
        app,
        ["list", "-c", str(temp_config), "-d", str(temp_data_dir)],
    )
    assert result.exit_code == 0
    assert "Mexico vs South Africa" in result.stdout
    assert "29 fixtures" in result.stdout
