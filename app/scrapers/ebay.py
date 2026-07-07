from .base import BaseScraper
import logging

logger = logging.getLogger(__name__)

class EbayScraper(BaseScraper):
    def __init__(self):
        super().__init__("ebay")

    async def search(self, query: str, filters: dict = None) -> list:
        logger.warning("Ebay search not implemented yet")
        return []

    async def scrape_listing(self, url: str) -> dict:
        logger.warning("Ebay scraping not implemented yet")
        return {}