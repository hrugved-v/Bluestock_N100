from src.etl.loader import ExcelLoader

loader = ExcelLoader()

data = loader.load_all("data/raw")

for name, df in data.items():
    print("\n", name)
    print(df.shape)