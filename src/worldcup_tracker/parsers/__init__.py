from worldcup_tracker.parsers.base import ParserRegistry, get_parser
from worldcup_tracker.parsers.big_penny import BigPennyParser
from worldcup_tracker.parsers.urban_pubs import UrbanPubsParser

__all__ = ["BigPennyParser", "ParserRegistry", "UrbanPubsParser", "get_parser"]

# Register built-in parsers
ParserRegistry.register("urban_pubs", UrbanPubsParser())
ParserRegistry.register("big_penny", BigPennyParser())
