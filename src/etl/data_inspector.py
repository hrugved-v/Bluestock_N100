import pandas as pd

df = pd.read_excel(
    "data/raw/cashflow.xlsx",
    header=None
)

print(df.head(10))