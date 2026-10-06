"""Quotes to Scrape scraper."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
logger = logging.getLogger(__name__)

class QuotesScraper(BaseScraper):
    SOURCE, START_URL = "Quotes to Scrape", "https://quotes.toscrape.com/"
    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.pages_attempted = self.pages_succeeded = 0; self.errors = []

    def scrape(self):
        records, url, visited, page_number = [], self.START_URL, set(), 0
        while url and url not in visited:
            visited.add(url); page_number += 1; self.pages_attempted += 1
            logger.info("Quotes page %d: %s", page_number, url)
            response = self.fetch(url)
            if response is None:
                self.errors.append(f"page_failed:{url}"); break
            self.pages_succeeded += 1
            soup = BeautifulSoup(response.text, "lxml")
            for quote in soup.select("div.quote"):
                try: records.append(self._parse_quote(quote, url))
                except Exception as exc:
                    logger.warning("Could not parse quote on %s: %s", url, exc)
                    self.errors.append(f"record_parse_failed:{url}:{exc}")
            nxt = soup.select_one("li.next > a[href]")
            url = self.next_url(url, nxt.get("href") if nxt else None)
        return records

    def _parse_quote(self, quote, page_url):
        text, author = quote.select_one("span.text"), quote.select_one("small.author")
        if text is None or author is None: raise ValueError("missing quote text or author")
        return {"source": self.SOURCE, "source_url": page_url,
                "name_or_title": text.get_text(" ", strip=True), "category": None,
                "price": None, "rating": None, "author": author.get_text(" ", strip=True),
                "tags": [t.get_text(" ", strip=True) for t in quote.select("a.tag")],
                "description": None, "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
