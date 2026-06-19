
from src.etl.loader import ExcelLoader

loader = ExcelLoader()
data = loader.load_all("data/raw")

for name, df in data.items():
    print("\n" + "="*60)
    print(name.upper())
    print(df.columns.tolist())