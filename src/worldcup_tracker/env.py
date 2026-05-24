"""Load optional `.env` from the project directory."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_LOADED = False


def load_env_file() -> Path | None:
    """Load `.env` once. Returns the path loaded, or None if no file was found."""
    global _LOADED
    if _LOADED:
        return None

    candidates: list[Path] = []
    explicit = os.environ.get("WCT_ENV_FILE")
    if explicit:
        candidates.append(Path(explicit))
    candidates.append(Path.cwd() / ".env")

    for path in candidates:
        if path.is_file():
            load_dotenv(path, override=False)
            _LOADED = True
            return path

    _LOADED = True
    return None
