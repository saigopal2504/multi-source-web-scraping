from processing.cleaning import clean_price, clean_rating, clean_record, clean_tags, clean_text, normalize_url, strip_curly_quotes

def test_clean_text_collapses_whitespace(): assert clean_text("  Hello\xa0\n  World ") == "Hello World"
def test_clean_price_and_rating(): assert clean_price("£51.77") == 51.77 and clean_rating("star-rating Three") == 3
def test_tags_are_normalized(): assert clean_tags(["life", "  wisdom", "life"]) == "life;wisdom"
def test_quote_and_url_cleaning(): assert strip_curly_quotes("“A quote”") == "A quote" and normalize_url(" https://example.com/item ") == "https://example.com/item"
def test_clean_record_standardizes_values():
    r = clean_record({"source":"Books to Scrape","source_url":"https://example.com","name_or_title":" A ","price":"£1.20","rating":"Five","scraped_at":"now"})
    assert r["name_or_title"] == "A" and r["price"] == 1.2 and r["rating"] == 5
