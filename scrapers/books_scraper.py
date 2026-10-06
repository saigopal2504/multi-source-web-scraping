"""Books to Scrape scraper."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
logger = logging.getLogger(__name__)

class BooksScraper(BaseScraper):
    SOURCE, START_URL = "Books to Scrape", "https://books.toscrape.com/"
    def __init__(self, *, fetch_details=True, **kwargs):
        super().__init__(**kwargs); self.fetch_details = fetch_details
        self.pages_attempted = self.pages_succeeded = 0
        self.detail_pages_attempted = self.detail_pages_succeeded = 0
        self.errors = []

    def scrape(self):
        records, url, visited, page_number = [], self.START_URL, set(), 0
        while url and url not in visited:
            visited.add(url); page_number += 1; self.pages_attempted += 1
            logger.info("Books page %d: %s", page_number, url)
            response = self.fetch(url)
            if response is None:
                self.errors.append(f"list_page_failed:{url}"); break
            self.pages_succeeded += 1
            soup = BeautifulSoup(response.text, "lxml")
            for article in soup.select("article.product_pod"):
                try:
                    record = self._parse_listing(article, url)
                    if self.fetch_details and record.get("source_url"):
                        self._add_details(record, record["source_url"])
                    records.append(record)
                except Exception as exc:
                    logger.warning("Could not parse book on %s: %s", url, exc)
                    self.errors.append(f"record_parse_failed:{url}:{exc}")
            nxt = soup.select_one("li.next > a[href]")
            url = self.next_url(url, nxt.get("href") if nxt else None)
        return records

    def _parse_listing(self, article, page_url):
        link = article.select_one("h3 > a[href]")
        price = article.select_one("p.price_color")
        rating = article.select_one("p.star-rating")
        if link is None: raise ValueError("missing book link")
        href = link.get("href")
        return {"source": self.SOURCE, "source_url": urljoin(page_url, href) if href else None,
                "name_or_title": link.get("title") or link.get_text(" ", strip=True),
                "category": None, "price": price.get_text(" ", strip=True) if price else None,
                "rating": " ".join(rating.get("class", [])) if rating else None,
                "author": None, "tags": None, "description": None,
                "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    def _add_details(self, record, detail_url):
        self.detail_pages_attempted += 1
        response = self.fetch(detail_url)
        if response is None:
            self.errors.append(f"detail_page_failed:{detail_url}"); return
        self.detail_pages_succeeded += 1
        soup = BeautifulSoup(response.text, "lxml")
        crumbs = soup.select("ul.breadcrumb li a")
        if crumbs: record["category"] = crumbs[-1].get_text(" ", strip=True)
        heading = soup.select_one("#product_description")
        if heading:
            description = heading.find_next_sibling("p")
            if description: record["description"] = description.get_text(" ", strip=True)
