from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_HTML = FIXTURES_DIR / "bar_kick_sample.html"


@pytest.fixture
def sample_html() -> str:
    return SAMPLE_HTML.read_text(encoding="utf-8")


@pytest.fixture
def bar_kick_url() -> str:
    return (
        "https://www.urbanpubsandbars.com/world-cup-2026/"
        "bar-kick-at-the-shoreditch-arms"
    )


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    return data


@pytest.fixture
def temp_config(tmp_path: Path, bar_kick_url: str) -> Path:
    config = tmp_path / "config.yaml"
    config.write_text(
        f"""venues:
  - name: "Bar Kick at The Shoreditch Arms"
    url: "{bar_kick_url}"
    parser: urban_pubs
fetch:
  timeout_seconds: 5
""",
        encoding="utf-8",
    )
    return config
