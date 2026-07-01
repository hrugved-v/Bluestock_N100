from src.analytics.ratios import (
    RatioInputs,
    asset_turnover,
    calculate_all_ratios,
    debt_to_equity,
    interest_coverage,
    is_financial_sector,
    net_debt,
    net_profit_margin,
    operating_profit_margin,
    return_on_assets,
    return_on_capital_employed,
    return_on_equity,
    safe_divide,
    shareholder_equity,
)


def test_safe_divide_returns_value():
    result = safe_divide(25, 100, multiplier=100, metric_name="test")

    assert result.value == 25.0
    assert result.flag is None


def test_safe_divide_flags_zero_denominator():
    result = safe_divide(25, 0, metric_name="test")

    assert result.value is None
    assert result.flag == "zero_denominator"


def test_safe_divide_flags_missing_input():
    result = safe_divide(None, 100, metric_name="test")

    assert result.value is None
    assert result.flag == "missing_input"


def test_shareholder_equity_adds_capital_and_reserves():
    assert shareholder_equity(100, 250) == 350


def test_shareholder_equity_returns_none_for_missing_value():
    assert shareholder_equity(100, None) is None


def test_financial_sector_detects_bank():
    assert is_financial_sector("Financial Services", "Private Bank")


def test_financial_sector_detects_insurance():
    assert is_financial_sector("Services", "Life Insurance")


def test_financial_sector_returns_false_for_non_finance():
    assert not is_financial_sector("Information Technology", "Software")


def test_net_profit_margin_calculates_percentage():
    assert net_profit_margin(120, 1000).value == 12.0


def test_net_profit_margin_flags_zero_sales():
    assert net_profit_margin(120, 0).flag == "zero_denominator"


def test_operating_profit_margin_calculates_percentage():
    assert operating_profit_margin(200, 1000).value == 20.0


def test_return_on_equity_calculates_percentage():
    result = return_on_equity(50, 100, 150)

    assert result.value == 20.0
    assert result.flag is None


def test_return_on_equity_flags_negative_equity():
    result = return_on_equity(50, 100, -200)

    assert result.value is None
    assert result.flag == "negative_equity"


def test_roce_calculates_ebit_over_capital_employed():
    result = return_on_capital_employed(80, 20, 100, 100, 200)

    assert result.value == 25.0


def test_roce_flags_financial_sector_carve_out():
    result = return_on_capital_employed(
        80,
        20,
        100,
        100,
        200,
        financial_sector=True,
    )

    assert result.value is None
    assert result.flag == "financial_sector_not_applicable"


def test_roce_flags_non_positive_capital_employed():
    result = return_on_capital_employed(80, 20, 100, -250, 100)

    assert result.value is None
    assert result.flag == "non_positive_capital_employed"


def test_return_on_assets_calculates_percentage():
    assert return_on_assets(75, 1500).value == 5.0


def test_debt_to_equity_calculates_ratio():
    assert debt_to_equity(300, 100, 200).value == 1.0


def test_debt_to_equity_flags_debt_free_company():
    result = debt_to_equity(0, 100, 200)

    assert result.value == 0.0
    assert result.flag == "debt_free"


def test_debt_to_equity_returns_zero_for_debt_free_company_even_without_equity():
    result = debt_to_equity(0, 100, -100)

    assert result.value == 0.0
    assert result.flag == "debt_free"


def test_debt_to_equity_flags_non_positive_equity():
    result = debt_to_equity(100, 50, -100)

    assert result.value is None
    assert result.flag == "non_positive_equity"


def test_debt_to_equity_flags_zero_denominator():
    result = debt_to_equity(100, 50, -50)

    assert result.value is None
    assert result.flag == "non_positive_equity"


def test_debt_to_equity_sets_high_leverage_flag_for_non_financial_company():
    result = debt_to_equity(600, 50, 50, broad_sector="Industrials")

    assert result.value == 6.0
    assert result.high_leverage_flag is True


def test_debt_to_equity_suppresses_high_leverage_flag_for_financials():
    result = debt_to_equity(600, 50, 50, broad_sector="Financials")

    assert result.value == 6.0
    assert result.high_leverage_flag is False


def test_debt_to_equity_suppresses_high_leverage_flag_for_detected_financial_sector():
    result = debt_to_equity(600, 50, 50, financial_sector=True)

    assert result.value == 6.0
    assert result.high_leverage_flag is False


def test_interest_coverage_calculates_ratio():
    assert interest_coverage(250, 50).value == 5.0


def test_interest_coverage_includes_other_income():
    assert interest_coverage(100, 50, other_income=25).value == 2.5


def test_interest_coverage_flags_debt_free_zero_interest():
    result = interest_coverage(250, 0, borrowings=0)

    assert result.value is None
    assert result.flag == "debt_free"
    assert result.label == "Debt Free"


def test_interest_coverage_flags_no_interest_expense():
    result = interest_coverage(250, 0, borrowings=100)

    assert result.value is None
    assert result.flag == "no_interest_expense"
    assert result.label == "Debt Free"


def test_interest_coverage_sets_warning_below_threshold():
    result = interest_coverage(100, 100, other_income=25)

    assert result.value == 1.25
    assert result.interest_coverage_warning is True


def test_interest_coverage_does_not_warn_at_threshold():
    result = interest_coverage(100, 100, other_income=50)

    assert result.value == 1.5
    assert result.interest_coverage_warning is False


def test_net_debt_subtracts_investments():
    assert net_debt(500, 125).value == 375.0


def test_net_debt_can_be_negative_for_net_cash():
    assert net_debt(100, 250).value == -150.0


def test_asset_turnover_calculates_ratio():
    assert asset_turnover(1000, 2000).value == 0.5


def test_asset_turnover_returns_none_for_zero_assets():
    result = asset_turnover(1000, 0)

    assert result.value is None
    assert result.flag == "zero_denominator"


def test_asset_turnover_still_calculates_for_financial_sector():
    result = asset_turnover(1000, 2000, financial_sector=True)

    assert result.value == 0.5
    assert result.flag is None


def test_calculate_all_ratios_returns_expected_keys():
    result = calculate_all_ratios(
        RatioInputs(
            sales=1000,
            operating_profit=200,
            other_income=40,
            net_profit=100,
            profit_before_tax=120,
            interest=30,
            equity_capital=100,
            reserves=400,
            borrowings=250,
            investments=50,
            total_assets=1500,
            broad_sector="Consumer",
            sub_sector="FMCG",
        )
    )

    assert set(result) == {
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "roce_pct",
        "return_on_assets_pct",
        "debt_to_equity",
        "interest_coverage",
        "net_debt_cr",
        "asset_turnover",
    }
    assert result["net_profit_margin_pct"].value == 10.0
    assert result["debt_to_equity"].value == 0.5
    assert result["interest_coverage"].value == 8.0


def test_calculate_all_ratios_applies_financial_sector_carve_outs():
    result = calculate_all_ratios(
        RatioInputs(
            sales=1000,
            operating_profit=200,
            other_income=40,
            net_profit=100,
            profit_before_tax=120,
            interest=30,
            equity_capital=100,
            reserves=400,
            borrowings=250,
            investments=50,
            total_assets=1500,
            broad_sector="Financial Services",
            sub_sector="Bank",
        )
    )

    assert result["debt_to_equity"].value == 0.5
    assert result["debt_to_equity"].high_leverage_flag is False
    assert result["interest_coverage"].flag == "financial_sector_not_applicable"
    assert result["asset_turnover"].value == 0.67
