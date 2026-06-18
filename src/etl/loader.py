import pandas as pd

class ExcelLoader:

    def __init__(self, filepath):
        self.filepath = filepath

    def load(self):

        df = pd.read_excel(self.filepath)

        print(f"Loaded {len(df)} rows")

        return df
