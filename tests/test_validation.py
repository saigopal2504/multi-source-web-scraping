from processing.validation import validate_record

def valid_record(): return {"source":"Books to Scrape","source_url":"https://example.com/book","name_or_title":"A book","price":10.5,"rating":4,"scraped_at":"2026-01-01T00:00:00+00:00"}
def test_valid_record_has_no_errors(): assert validate_record(valid_record()) == []
def test_invalid_values_return_reasons():
    record = valid_record(); record.update({"source":"Other","source_url":"not-a-url","name_or_title":"","price":-1,"rating":6})
    assert {"unknown_source","invalid_source_url","missing_name_or_title","invalid_price","invalid_rating"}.issubset(validate_record(record))
