import pandas as pd


class DataValidator:

    def __init__(self):
        self.failures = []

    def log_failure(self, rule_id, severity, table_name, message):

        self.failures.append({
            "rule_id": rule_id,
            "severity": severity,
            "table_name": table_name,
            "message": message
        })

    # DQ-01
    def check_pk_uniqueness(self, df, table_name):

        if "id" not in df.columns:
            return

        duplicates = df[df.duplicated(subset=["id"])]

        if len(duplicates) > 0:
            self.log_failure(
                "DQ-01",
                "CRITICAL",
                table_name,
                f"{len(duplicates)} duplicate primary keys"
            )

    # DQ-02
    def check_company_year_uniqueness(self, df, table_name):

        required_cols = ["company_id", "year"]

        if not all(col in df.columns for col in required_cols):
            return

        duplicates = df[
            df.duplicated(
                subset=["company_id", "year"]
            )
        ]

        if len(duplicates) > 0:
            self.log_failure(
                "DQ-02",
                "CRITICAL",
                table_name,
                f"{len(duplicates)} duplicate company-year rows"
            )

    # DQ-03
    def check_fk_integrity(
        self,
        child_df,
        valid_company_ids,
        table_name
    ):

        if "company_id" not in child_df.columns:
            return

        invalid = child_df[
            ~child_df["company_id"].isin(valid_company_ids)
        ]

        if len(invalid) > 0:
            self.log_failure(
                "DQ-03",
                "CRITICAL",
                table_name,
                f"{len(invalid)} invalid company references"
            )

    # DQ-04
    def check_balance_sheet(self, df):

        required_cols = [
            "total_assets",
            "total_liabilities"
        ]

        if not all(col in df.columns for col in required_cols):
            return

        invalid = df[
            (
                abs(
                    df["total_assets"]
                    - df["total_liabilities"]
                )
                / df["total_assets"]
            ) > 0.01
        ]

        if len(invalid) > 0:
            self.log_failure(
                "DQ-04",
                "WARNING",
                "balancesheet",
                f"{len(invalid)} balance mismatches"
            )

    # DQ-05
    def check_opm(self, df):

        required_cols = [
            "sales",
            "operating_profit",
            "opm_percentage"
        ]

        if not all(col in df.columns for col in required_cols):
            return

        calculated_opm = (
            df["operating_profit"]
            / df["sales"]
        ) * 100

        invalid = df[
            abs(
                calculated_opm
                - df["opm_percentage"]
            ) > 1
        ]

        if len(invalid) > 0:
            self.log_failure(
                "DQ-05",
                "WARNING",
                "profitandloss",
                f"{len(invalid)} OPM mismatches"
            )

    # DQ-06
    def check_positive_sales(self, df):

        if "sales" not in df.columns:
            return

        invalid = df[
            df["sales"] <= 0
        ]

        if len(invalid) > 0:
            self.log_failure(
                "DQ-06",
                "WARNING",
                "profitandloss",
                f"{len(invalid)} non-positive sales values"
            )

    def export_failures(self, filepath):

        df = pd.DataFrame(self.failures)

        if df.empty:
            df = pd.DataFrame(columns=[
                "rule_id",
                "severity",
                "table_name",
                "message"
            ])

        df.to_csv(filepath, index=False)