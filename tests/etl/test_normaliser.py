from src.etl.normaliser import (
    normalize_year,
    normalize_ticker
)
def test_year_numeric():
    assert normalize_year(2023) == 2023


def test_year_short():
    assert normalize_year(23) == 2023


def test_year_fy():
    assert normalize_year("FY23") == 2023


def test_year_none():
    assert normalize_year(None) is None


def test_year_invalid():
    assert normalize_year("ABC") is None

def test_ticker_lower():
    assert normalize_ticker("tcs") == "TCS"


def test_ticker_ns():
    assert normalize_ticker("TCS.NS") == "TCS"


def test_ticker_eq():
    assert normalize_ticker("TCS-EQ") == "TCS"


def test_ticker_spaces():
    assert normalize_ticker(" tcs ") == "TCS"


def test_ticker_none():
    assert normalize_ticker(None) is None