import sqlite3
import pandas as pd

conn = sqlite3.connect("nifty100.db")

df = pd.read_excel(
    "data/raw/companies.xlsx",
    skiprows=1
)

df.columns = [
    "id",
    "company_logo",
    "company_name",
    "chart_link",
    "about_company",
    "website",
    "nse_profile",
    "bse_profile",
    "face_value",
    "book_value",
    "roce_percentage",
    "roe_percentage"
]

df.to_sql(
    "companies",
    conn,
    if_exists="append",
    index=False
)

print("Companies Loaded:", len(df))

conn.close()