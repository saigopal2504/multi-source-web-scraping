"""Validation rules for standardized records."""
from __future__ import annotations
import math
from numbers import Real
from urllib.parse import urlparse
VALID_SOURCES = {"Books to Scrape", "Quotes to Scrape"}

def validate_record(record: dict) -> list[str]:
    problems = []
    if record.get("source") not in VALID_SOURCES: problems.append("unknown_source")
    if not record.get("name_or_title"): problems.append("missing_name_or_title")
    parsed = urlparse(str(record.get("source_url") or ""))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc: problems.append("invalid_source_url")
    price = record.get("price")
    if price is not None and (isinstance(price, bool) or not isinstance(price, Real) or not math.isfinite(float(price)) or price < 0): problems.append("invalid_price")
    rating = record.get("rating")
    if rating is not None and (isinstance(rating, bool) or not isinstance(rating, int) or rating not in range(1, 6)): problems.append("invalid_rating")
    if not record.get("scraped_at"): problems.append("missing_scraped_at")
    return problems
