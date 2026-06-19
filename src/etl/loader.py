import pandas as pd
from pathlib import Path


class ExcelLoader:

    HEADER1_FILES = {
        "analysis",
        "balancesheet",
        "cashflow",
        "companies",
        "documents",
        "profitandloss",
        "prosandcons"
    }

    def load_excel(self, filepath):

        stem = Path(filepath).stem

        header_row = 1 if stem in self.HEADER1_FILES else 0

        return pd.read_excel(
            filepath,
            header=header_row
        )

    def load_all(self, data_dir):

        datasets = {}

        for file in Path(data_dir).glob("*.xlsx"):
            datasets[file.stem] = self.load_excel(file)

        return datasets