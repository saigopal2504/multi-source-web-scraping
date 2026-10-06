"""Shared HTTP behaviour for the assignment scrapers."""
from __future__ import annotations
import logging, time
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, *, timeout=20.0, request_delay=0.2,
                 user_agent="PythonWebScrapingAssignment/1.0 (educational project)"):
        self.timeout, self.request_delay = timeout, max(0.0, request_delay)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        retry = Retry(total=3, connect=3, read=3, status=3, backoff_factor=0.75,
                      status_forcelist=(429, 500, 502, 503, 504),
                      allowed_methods=frozenset({"GET"}), raise_on_status=False)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter); self.session.mount("https://", adapter)

    def fetch(self, url):
        try:
            logger.debug("GET %s", url)
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.encoding or "utf-8"
            return response
        except requests.RequestException as exc:
            logger.error("Request failed for %s: %s", url, exc)
            return None
        finally:
            if self.request_delay: time.sleep(self.request_delay)

    @staticmethod
    def next_url(current_url, href):
        if not href: return None
        candidate = urljoin(current_url, href.strip())
        return candidate if candidate.startswith(("http://", "https://")) else None

    def close(self): self.session.close()
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): self.close()
