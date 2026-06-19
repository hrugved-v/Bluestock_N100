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

def test_year_fy22():
    assert normalize_year("FY22") == 2022

def test_year_fy_space():
    assert normalize_year("FY 22") == 2022

def test_year_long():
    assert normalize_year("2022") == 2022

def test_year_whitespace():
    assert normalize_year(" 2022 ") == 2022

def test_year_empty():
    assert normalize_year("") is None

def test_year_invalid():
    assert normalize_year("ABC") is None

def test_ticker_mixed_case():
    assert normalize_ticker("TcS") == "TCS"

def test_ticker_multiple_spaces():
    assert normalize_ticker(" TCS ") == "TCS"

def test_ticker_ns_lower():
    assert normalize_ticker("tcs.ns") == "TCS"

def test_ticker_eq_lower():
    assert normalize_ticker("tcs-eq") == "TCS"

def test_ticker_empty():
    assert normalize_ticker("") == ""