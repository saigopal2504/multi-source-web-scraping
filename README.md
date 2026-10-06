# Multi-Source Web Scraping & Data Consolidation

A reproducible Python ETL pipeline for the interview assignment. It collects all available pages from **Books to Scrape** and **Quotes to Scrape**, standardizes the two source shapes, validates the results, removes normalized duplicates, and writes a consolidated CSV plus a JSON summary.

## Quick start

Requirements: Python 3.10-3.12 recommended and internet access to the two public practice sites.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python main.py
```

The command creates or replaces:

- `output/final_dataset.csv`
- `output/summary_report.json`
- `logs/scraper.log`

Optional arguments:

```text
python main.py --delay 0.5             # slower, more conservative request pacing
python main.py --skip-book-details    # scrape listing pages only
python main.py --timeout 30 --verbose  # change timeout and enable debug logs
```

## Source exploration

Both sites are server-rendered HTML, so Requests + BeautifulSoup is sufficient and avoids the overhead of Selenium/Playwright.

| Source | Record selector | Important fields | Pagination |
|---|---|---|---|
| Books to Scrape | `article.product_pod` | `h3 > a`, `p.price_color`, `p.star-rating` | `li.next > a` |
| Quotes to Scrape | `div.quote` | `span.text`, `small.author`, `a.tag` | `li.next > a` |

Book listing cards do not contain category or description. The default scraper follows each book URL and reads category from the breadcrumb and description from the `#product_description` section. Use `--skip-book-details` when a fast listing-only run is preferred; those fields then remain empty.

The quote `source_url` is the page on which the quote was found. The assignment only requires a stable original source URL; an author page is not used as a substitute for the quote's listing page.

## Pipeline design

```text
HTTP fetch -> source parsers -> cleaning -> validation -> deduplication -> CSV/JSON
```

- `scrapers/base_scraper.py` contains one shared HTTP session, User-Agent, timeout, retries for transient status codes, and request pacing.
- `scrapers/books_scraper.py` and `scrapers/quotes_scraper.py` isolate source-specific selectors and follow the live next link until it disappears.
- `processing/cleaning.py` contains pure normalization functions.
- `processing/validation.py` returns all rejection reasons for a record rather than raising.
- `processing/deduplication.py` creates deterministic SHA-256 fingerprints.
- `main.py` coordinates the stages and writes outputs.

A failed page is logged and stops only that source; the other source still runs. A malformed individual record is logged and skipped. Retries cover connection/read problems and HTTP 429/500/502/503/504 responses.

## Standard data model

| Column | Books to Scrape | Quotes to Scrape |
|---|---|---|
| `source` | `Books to Scrape` | `Quotes to Scrape` |
| `source_url` | absolute book detail URL | page URL containing the quote |
| `name_or_title` | book title | quote text |
| `category` | book category from detail page | empty |
| `price` | numeric GBP value | empty |
| `rating` | integer 1-5 | empty |
| `author` | empty | author name |
| `tags` | empty | normalized, lower-case, alphabetically sorted tags joined by `;` |
| `description` | book description when available | empty |
| `scraped_at` | UTC ISO-8601 timestamp | UTC ISO-8601 timestamp |

Source-specific fields are represented as empty CSV cells (`None` in Python). No values are invented.

## Cleaning and validation

Cleaning collapses whitespace, removes decorative curly quotation marks, converts prices such as `£51.77` to floats, converts word ratings (`One` through `Five`) to integers, normalizes quote tags, accepts only absolute HTTP/HTTPS URLs, and converts empty values to `None`.

A record is accepted only when it has a recognized source, non-empty title/text, valid source URL, and timestamp. If price exists it must be a finite non-negative number; if rating exists it must be an integer from 1 to 5. Rejected records and reason counts are retained in the summary report/log.

## Duplicate strategy

Duplicates are removed, keeping the first occurrence. The fingerprint is built after normalization, lowercasing text, removing punctuation, and collapsing whitespace:

- Books: source + normalized book title.
- Quotes: source + normalized author + first 50 normalized characters of quote text.

This catches differences such as `Example Book`, ` example book `, and `EXAMPLE BOOK`. The source is included so records from different sites are not accidentally merged. Unit tests include deliberate duplicates even though the practice sites normally contain unique records.

## Outputs

`final_dataset.csv` uses a fixed UTF-8 column order. `summary_report.json` contains per-source page/request counts, raw records, cleaned records, rejected records and rejection reasons, duplicates, final records, errors, timing, and a reconciliation boolean. `logs/scraper.log` contains timestamps, page progress, warnings, and errors.

The expected live run is approximately 1,000 books over 50 pages plus 100 quotes over 10 pages. The exact count may change if the public practice sites change.

## Testing

Tests do not require internet access:

```bash
python -m pytest -q
```

They cover whitespace/URL/number/tag cleaning, validation failures, and duplicate fingerprints. For a clean-environment verification, create a new virtual environment, install only `requirements.txt`, run tests, then run `python main.py`.

## Assumptions and limitations

- The two supplied sites remain publicly accessible and retain their current server-rendered structure.
- The scraper does not bypass authentication, CAPTCHA, robots controls, or access restrictions.
- Details add approximately one request per book. Use `--skip-book-details` if the reviewer wants a faster run.
- If a detail page fails, the book listing row is retained and only category/description may be empty.
- Because the pipeline follows `next` links, it stops when the site provides no next link or a repeated URL is encountered.
- This is an interview-scale batch job, not a production scheduler or database loader.

## Project structure

```text
scraping_assignment/
├── scrapers/
│   ├── base_scraper.py
│   ├── books_scraper.py
│   └── quotes_scraper.py
├── processing/
│   ├── cleaning.py
│   ├── validation.py
│   └── deduplication.py
├── tests/
├── output/
├── logs/
├── main.py
├── requirements.txt
├── README.md
└── AI_USAGE.md
```

## Interview talking points

- Requests + BeautifulSoup fits plain HTML and is simpler than a browser automation stack.
- Pagination is dynamic: the parser resolves `li.next > a` with `urljoin` and stops when absent.
- Missing selectors are handled with checks; one bad record/page is isolated.
- Retry policy handles temporary failures, while per-source exception handling protects the other source.
- Cleaning is separate from parsing, which keeps source selectors independent from business rules.
- The final run and tests should be re-run before submission because the sites are public and can change.

See `AI_USAGE.md` for the required AI-use disclosure.
