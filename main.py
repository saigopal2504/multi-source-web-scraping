"""Run the complete multi-source scraping ETL pipeline."""
from __future__ import annotations
import argparse, csv, json, logging, sys, time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from processing.cleaning import clean_record
from processing.deduplication import find_duplicates
from processing.validation import validate_record
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper
ROOT = Path(__file__).resolve().parent; OUTPUT_DIR = ROOT / "output"; LOG_DIR = ROOT / "logs"
CSV_COLUMNS = ["source","source_url","name_or_title","category","price","rating","author","tags","description","scraped_at"]
SOURCES = ("Books to Scrape", "Quotes to Scrape")

def configure_logging(path, verbose=False):
    path.parent.mkdir(parents=True, exist_ok=True); logger = logging.getLogger(); logger.setLevel(logging.DEBUG if verbose else logging.INFO); logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    fh = logging.FileHandler(path, encoding="utf-8"); fh.setFormatter(formatter); ch = logging.StreamHandler(); ch.setFormatter(formatter); logger.addHandler(fh); logger.addHandler(ch)

def parse_args():
    p = argparse.ArgumentParser(description="Scrape and consolidate Books to Scrape and Quotes to Scrape")
    p.add_argument("--delay", type=float, default=0.2, help="Seconds between requests")
    p.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds")
    p.add_argument("--skip-book-details", action="store_true", help="Do not request individual book pages")
    p.add_argument("--verbose", action="store_true"); return p.parse_args()

def empty_metrics():
    return {"pages_attempted":0,"pages_succeeded":0,"raw_records_collected":0,"records_after_cleaning":0,"records_rejected":0,"rejection_reasons":{},"duplicates_detected":0,"final_records":0,"errors":[]}

def scrape_sources(args):
    raw, metrics = [], {source: empty_metrics() for source in SOURCES}
    specs = [("Books to Scrape", BooksScraper, {"fetch_details": not args.skip_book_details}), ("Quotes to Scrape", QuotesScraper, {})]
    for source, cls, extra in specs:
        scraper = cls(timeout=args.timeout, request_delay=args.delay, **extra)
        try:
            records = scraper.scrape(); raw.extend(records); m = metrics[source]
            m.update(pages_attempted=scraper.pages_attempted, pages_succeeded=scraper.pages_succeeded, raw_records_collected=len(records), errors=list(scraper.errors))
            if hasattr(scraper, "detail_pages_attempted"): m.update(detail_pages_attempted=scraper.detail_pages_attempted, detail_pages_succeeded=scraper.detail_pages_succeeded)
        except Exception:
            logging.getLogger(__name__).exception("Unexpected failure while scraping %s; continuing", source); metrics[source]["errors"].append("unexpected_scraper_failure")
        finally: scraper.close()
    return raw, metrics

def process_records(raw, metrics):
    valid, rejected, counts, reason_counts = [], [], Counter(), defaultdict(Counter)
    for item in raw:
        source = item.get("source") or "Unknown"; cleaned = clean_record(item); problems = validate_record(cleaned)
        if problems:
            rejected.append({"record": cleaned, "reasons": problems}); reason_counts[source].update(problems); logging.getLogger(__name__).warning("Rejected %s record: %s", source, ", ".join(problems))
        else: valid.append(cleaned); counts[source] += 1
    for source in SOURCES:
        metrics[source]["records_after_cleaning"] = counts[source] + sum(1 for item in rejected if (item["record"].get("source") or "Unknown") == source); metrics[source]["records_rejected"] = sum(1 for item in rejected if (item["record"].get("source") or "Unknown") == source); metrics[source]["rejection_reasons"] = dict(reason_counts[source])
    unique, duplicates = find_duplicates(valid); dup_counts = Counter(x.get("source", "Unknown") for x in duplicates)
    for source in SOURCES:
        metrics[source]["duplicates_detected"] = dup_counts[source]; metrics[source]["final_records"] = sum(x.get("source") == source for x in unique)
    return unique, duplicates, rejected

def write_csv(records, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore"); writer.writeheader(); writer.writerows({c:r.get(c) for c in CSV_COLUMNS} for r in records)

def write_json(report, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f: json.dump(report, f, indent=2, ensure_ascii=False); f.write("\n")

def build_report(started, ended, duration, metrics, duplicates, rejected, final_count):
    totals = {"raw_records_collected":sum(m["raw_records_collected"] for m in metrics.values()),"records_after_cleaning":sum(m["records_after_cleaning"] for m in metrics.values()),"records_rejected":sum(m["records_rejected"] for m in metrics.values()),"duplicates_detected":len(duplicates),"final_records":final_count}
    reasons = Counter(reason for item in rejected for reason in item["reasons"])
    return {"assignment":"Multi-Source Web Scraping & Data Consolidation","started_at_utc":started,"ended_at_utc":ended,"duration_seconds":round(duration,3),"sources":metrics,"totals":totals,"total_rejection_reasons":dict(reasons),"reconciliation":{"cleaned_minus_rejected_minus_duplicates_equals_final":totals["records_after_cleaning"]-totals["records_rejected"]-totals["duplicates_detected"] == final_count}}

def main():
    args = parse_args(); configure_logging(LOG_DIR / "scraper.log", args.verbose); logger = logging.getLogger(__name__); started_at = datetime.now(timezone.utc).isoformat(timespec="seconds"); begin = time.monotonic(); logger.info("Starting scraping pipeline")
    raw, metrics = scrape_sources(args); logger.info("Collected %d raw records", len(raw)); valid, duplicates, rejected = process_records(raw, metrics); ended_at = datetime.now(timezone.utc).isoformat(timespec="seconds"); report = build_report(started_at, ended_at, time.monotonic()-begin, metrics, duplicates, rejected, len(valid)); write_csv(valid, OUTPUT_DIR / "final_dataset.csv"); write_json(report, OUTPUT_DIR / "summary_report.json"); logger.info("Finished: %d unique valid records, %d duplicates", len(valid), len(duplicates)); return 0

if __name__ == "__main__": sys.exit(main())
