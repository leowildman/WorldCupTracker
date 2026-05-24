from worldcup_tracker.parsers.base import ParserRegistry, get_parser
from worldcup_tracker.parsers.urban_pubs import UrbanPubsParser

__all__ = ["ParserRegistry", "UrbanPubsParser", "get_parser"]

# Register built-in parsers
ParserRegistry.register("urban_pubs", UrbanPubsParser())
