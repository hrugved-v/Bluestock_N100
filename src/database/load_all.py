import sqlite3
import pandas as pd

conn = sqlite3.connect("nifty100.db")

files = {
    "profitandloss": ("data/raw/profitandloss.xlsx", 1),
    "balancesheet": ("data/raw/balancesheet.xlsx", 1),
    "cashflow": ("data/raw/cashflow.xlsx", 1),
    "analysis": ("data/raw/analysis.xlsx", 1),
    "documents": ("data/raw/documents.xlsx", 1),
    "prosandcons": ("data/raw/prosandcons.xlsx", 1),

    "financial_ratios": ("data/raw/financial_ratios.xlsx", 0),
    "market_cap": ("data/raw/market_cap.xlsx", 0),
    "peer_groups": ("data/raw/peer_groups.xlsx", 0),
    "sectors": ("data/raw/sectors.xlsx", 0),
    "stock_prices": ("data/raw/stock_prices.xlsx", 0)
}

for table, (path, skip) in files.items():

    df = pd.read_excel(
        path,
        skiprows=skip
    )

    df.to_sql(
        table,
        conn,
        if_exists="append",
        index=False
    )

    print(
        f"{table}: {len(df)} rows loaded"
    )

conn.commit()
conn.close()

print("\nAll tables loaded successfully.")