from processing.deduplication import find_duplicates, make_fingerprint

def test_books_ignore_case_and_spaces():
    base = {"source":"Books to Scrape","author":None}; records = [{**base,"name_or_title":"Example Book Title"},{**base,"name_or_title":"  Example Book Title "},{**base,"name_or_title":"EXAMPLE BOOK TITLE"}]
    unique, duplicates = find_duplicates(records); assert len(unique) == 1 and len(duplicates) == 2

def test_quote_identity_includes_author():
    quote = {"source":"Quotes to Scrape","name_or_title":"Same text","author":"One"}; other = {**quote,"author":"Two"}
    assert make_fingerprint(quote) != make_fingerprint(other)
