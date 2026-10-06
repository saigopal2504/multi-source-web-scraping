"""Pure cleaning and normalization functions."""
from __future__ import annotations
import re
from typing import Any
from urllib.parse import urlparse
RATING_MAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

def clean_text(value: Any) -> str | None:
    if value is None: return None
    text = " ".join(str(value).replace("\xa0", " ").split())
    return text or None

def strip_curly_quotes(value: str | None) -> str | None:
    text = clean_text(value)
    return text.strip("\"'“”‘’") or None if text else None

def clean_price(value: Any) -> float | None:
    text = clean_text(value)
    if not text: return None
    match = re.search(r"[-+]?\d+(?:[,.]\d+)?", text.replace(",", ""))
    return round(float(match.group()), 2) if match else None

def clean_rating(value: Any) -> int | None:
    text = str(value or "").lower()
    for word, number in RATING_MAP.items():
        if re.search(rf"\b{re.escape(word)}\b", text): return number
    match = re.search(r"\b([1-5])\b", text)
    return int(match.group(1)) if match else None

def clean_tags(value: Any) -> str | None:
    if value is None: return None
    values = re.split(r"[;,]", value) if isinstance(value, str) else value
    tags = sorted({clean_text(item).lower() for item in values if clean_text(item)})
    return ";".join(tags) if tags else None

def normalize_url(value: Any) -> str | None:
    text = clean_text(value)
    if not text: return None
    parsed = urlparse(text)
    return text if parsed.scheme in {"http", "https"} and parsed.netloc else None

def clean_record(raw: dict) -> dict:
    return {"source": clean_text(raw.get("source")), "source_url": normalize_url(raw.get("source_url")),
            "name_or_title": strip_curly_quotes(raw.get("name_or_title")), "category": clean_text(raw.get("category")),
            "price": clean_price(raw.get("price")), "rating": clean_rating(raw.get("rating")),
            "author": clean_text(raw.get("author")), "tags": clean_tags(raw.get("tags")),
            "description": clean_text(raw.get("description")), "scraped_at": clean_text(raw.get("scraped_at"))}
