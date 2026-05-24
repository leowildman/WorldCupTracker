from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from worldcup_tracker.models import Fixture


class VenueParser(ABC):
    """Parse fixture listings from a venue HTML page."""

    @abstractmethod
    def parse(
        self,
        html: str,
        *,
        source_url: str | None = None,
        venue_name: str | None = None,
    ) -> list[Fixture]:
        ...


class ParserRegistry:
    _parsers: ClassVar[dict[str, VenueParser]] = {}

    @classmethod
    def register(cls, name: str, parser: VenueParser) -> None:
        cls._parsers[name] = parser

    @classmethod
    def get(cls, name: str) -> VenueParser:
        try:
            return cls._parsers[name]
        except KeyError as exc:
            known = ", ".join(sorted(cls._parsers)) or "(none)"
            raise ValueError(f"Unknown parser '{name}'. Known parsers: {known}") from exc


def get_parser(name: str) -> VenueParser:
    return ParserRegistry.get(name)
