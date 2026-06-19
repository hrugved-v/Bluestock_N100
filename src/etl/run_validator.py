from pathlib import Path

from src.etl.loader import ExcelLoader
from src.etl.validator import DataValidator


print("Loading data...")

loader = ExcelLoader()
data = loader.load_all("data/raw")

validator = DataValidator()

print("Running validations...")

valid_company_ids = set(
    data["companies"]["id"]
)

# DQ-01

for table_name, df in data.items():

    validator.check_pk_uniqueness(
        df,
        table_name
    )

# DQ-02

for table in [
    "profitandloss",
    "balancesheet",
    "cashflow",
    "financial_ratios",
    "market_cap"
]:

    if table in data:

        validator.check_company_year_uniqueness(
            data[table],
            table
        )

# DQ-03

for table in [
    "profitandloss",
    "balancesheet",
    "cashflow",
    "financial_ratios",
    "market_cap",
    "documents",
    "prosandcons",
    "analysis",
    "sectors",
    "stock_prices"
]:

    if table in data:

        validator.check_fk_integrity(
            data[table],
            valid_company_ids,
            table
        )

# DQ-04

if "balancesheet" in data:
    validator.check_balance_sheet(
        data["balancesheet"]
    )

# DQ-05

if "profitandloss" in data:
    validator.check_opm(
        data["profitandloss"]
    )

# DQ-06

if "profitandloss" in data:
    validator.check_positive_sales(
        data["profitandloss"]
    )

# Ensure output folder exists

Path("output").mkdir(
    parents=True,
    exist_ok=True
)

validator.export_failures(
    "output/validation_failures.csv"
)

print()
print("=" * 50)
print(f"Failures Found: {len(validator.failures)}")
print("Report Saved: output/validation_failures.csv")
print("=" * 50)