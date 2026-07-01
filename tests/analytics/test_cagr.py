import pytest

from src.analytics.cagr import (
    CAGRCalculator,
    FLAG_BOTH_NEGATIVE,
    FLAG_DECLINE_TO_LOSS,
    FLAG_INSUFFICIENT_HISTORY,
    FLAG_TURNAROUND,
    FLAG_ZERO_BASE,
    YearlyValue,
    calculate_cagr,
)


def test_calculate_cagr_returns_normal_percentage():
    result = calculate_cagr(100, 200, 5)

    assert result.value == 14.87
    assert result.flag is None


def test_positive_to_positive_has_no_flag():
    result = calculate_cagr(250, 400, 3)

    assert result.value == pytest.approx(16.96)
    assert result.flag is None


def test_positive_to_negative_flags_decline_to_loss():
    result = calculate_cagr(100, -20, 3)

    assert result.value is None
    assert result.flag == FLAG_DECLINE_TO_LOSS


def test_negative_to_positive_flags_turnaround():
    result = calculate_cagr(-100, 50, 3)

    assert result.value is None
    assert result.flag == FLAG_TURNAROUND


def test_negative_to_negative_flags_both_negative():
    result = calculate_cagr(-100, -50, 3)

    assert result.value is None
    assert result.flag == FLAG_BOTH_NEGATIVE


def test_zero_base_flags_zero_base():
    result = calculate_cagr(0, 100, 3)

    assert result.value is None
    assert result.flag == FLAG_ZERO_BASE


def test_missing_values_flag_insufficient_history():
    result = calculate_cagr(None, 100, 3)

    assert result.value is None
    assert result.flag == FLAG_INSUFFICIENT_HISTORY


def test_calculator_computes_3_year_cagr_from_unsorted_records():
    calculator = CAGRCalculator()
    records = [
        YearlyValue(2024, 133.1),
        YearlyValue(2021, 100),
        YearlyValue(2023, 121),
        YearlyValue(2022, 110),
    ]

    result = calculator.calculate_for_window(records, 3)

    assert result.value == pytest.approx(10.0)
    assert result.flag is None


def test_calculator_computes_5_year_cagr_from_mapping_records():
    calculator = CAGRCalculator()
    records = [
        {"fiscal_year": 2019, "metric": 100},
        {"fiscal_year": 2020, "metric": 110},
        {"fiscal_year": 2021, "metric": 121},
        {"fiscal_year": 2022, "metric": 133.1},
        {"fiscal_year": 2023, "metric": 146.41},
        {"fiscal_year": 2024, "metric": 161.051},
    ]

    result = calculator.calculate_for_window(
        records,
        5,
        year_key="fiscal_year",
        value_key="metric",
    )

    assert result.value == pytest.approx(10.0)
    assert result.flag is None


def test_calculator_computes_10_year_cagr():
    calculator = CAGRCalculator()
    records = [
        YearlyValue(year, 100 * (1.1 ** (year - 2014)))
        for year in range(2014, 2025)
    ]

    result = calculator.calculate_for_window(records, 10)

    assert result.value == pytest.approx(10.0)
    assert result.flag is None


def test_missing_start_year_flags_insufficient_history():
    calculator = CAGRCalculator()
    records = [
        YearlyValue(2020, 100),
        YearlyValue(2022, 121),
        YearlyValue(2024, 146.41),
    ]

    result = calculator.calculate_for_window(records, 3)

    assert result.value is None
    assert result.flag == FLAG_INSUFFICIENT_HISTORY


def test_calculate_windows_reuses_engine_for_supported_periods():
    calculator = CAGRCalculator()
    records = [
        YearlyValue(year, 100 * (1.1 ** (year - 2014)))
        for year in range(2014, 2025)
    ]

    results = calculator.calculate_windows(records)

    assert set(results) == {3, 5, 10}
    assert all(result.value == pytest.approx(10.0) for result in results.values())
