# AI Usage

AI assistance was used transparently during development. The final implementation was reviewed, executed, and tested by the candidate.

## Tool used

- **Tool:** ChatGPT
- **Used for:** interpreting the assignment, proposing a modular ETL structure, reviewing pagination and retry patterns, suggesting unit-test cases, and improving documentation.

## Representative prompts

1. “Design a Python project structure for scraping Books to Scrape and Quotes to Scrape with separate scraper and processing modules.”
2. “Show how to follow a site's `li.next > a` link dynamically and resolve relative URLs safely.”
3. “Suggest unit tests for whitespace cleaning, rating conversion, validation, and duplicate detection.”

## AI-assisted parts

- Initial module boundaries and standardized schema.
- Drafting the shared `requests.Session` retry configuration.
- Drafting cleaning, validation, and fingerprinting helpers.
- Drafting README explanations and test scenarios.

## Human review and changes

- Verified selectors against the live HTML of both practice sites.
- Added per-source failure isolation so one source can fail without stopping the other.
- Added bounded pagination loops using visited URLs.
- Added individual book detail-page fetching for category and description, with graceful fallback when a detail page fails.
- Ensured missing source-specific fields remain empty rather than being invented.
- Checked numeric validation, CSV column order, summary reconciliation, and encoding.

## Incorrect or incomplete suggestions found

A generic approach would have left book category and description empty. That is valid under the assignment, but this final version fetches each book detail page when `--skip-book-details` is not supplied. The implementation also avoids treating boolean values as numeric prices or ratings.

## Verification

- Ran the unit test suite with `pytest`.
- Ran the full pipeline against both public sites.
- Checked that both source names appear in the final CSV.
- Checked that output row count matches the report's final count.
- Checked that prices are numeric/blank and ratings are in the range 1-5/blank.
- Reviewed the generated log for page progress and errors.
