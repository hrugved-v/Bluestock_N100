import re
def normalize_year(value):
    """
    Converts different year formats to integer.

    Examples:
    FY23 -> 2023
    FY 2023 -> 2023
    2023 -> 2023
    """
    
    if value is None:
        return None

    value = str(value).strip().upper()

    if value.isdigit():
        year = int(value)

        if year < 100:
            return 2000 + year

        return year

    match = re.search(r'(\d{2,4})', value)

    if match:
        year = int(match.group(1))

        if year < 100:
            return 2000 + year

        return year

    return None

def normalize_ticker(ticker):
    """
    Converts ticker symbols to a standard format.
    """

    if ticker is None:
        return None

    ticker = str(ticker).strip().upper()

    ticker = ticker.replace(".NS", "")
    ticker = ticker.replace("-EQ", "")
    ticker = ticker.replace(" ", "")

    return ticker

