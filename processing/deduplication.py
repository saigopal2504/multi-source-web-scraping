"""Deterministic duplicate detection."""
from __future__ import annotations
import hashlib, re, unicodedata

def normalize_key_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return " ".join(re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE).split())

def make_fingerprint(record: dict) -> str:
    source = normalize_key_text(record.get("source"))
    if record.get("source") == "Books to Scrape": identity = f"{source}|{normalize_key_text(record.get('name_or_title'))}"
    else: identity = f"{source}|{normalize_key_text(record.get('author'))}|{normalize_key_text(record.get('name_or_title'))[:50]}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()

def find_duplicates(records: list[dict]) -> tuple[list[dict], list[dict]]:
    seen, unique, duplicates = set(), [], []
    for record in records:
        fingerprint = make_fingerprint(record)
        if fingerprint in seen: duplicates.append(record)
        else: seen.add(fingerprint); unique.append(record)
    return unique, duplicates
