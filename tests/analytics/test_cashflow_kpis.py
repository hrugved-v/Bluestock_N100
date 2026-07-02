import csv

import pytest

from src.analytics.cashflow_kpis import (
    CashFlowInput,
    KPIValue,
    PATTERN_CASH_ACCUMULATOR,
    PATTERN_DISTRESS_SIGNAL,
    PATTERN_GROWTH_FUNDED_BY_DEBT,
    PATTERN_LIQUIDATING_ASSETS,
    PATTERN_MIXED,
    PATTERN_PRE_REVENUE,
    PATTERN_REINVESTOR,
    PATTERN_SHAREHOLDER_RETURNS,
    calculate_capex_intensity,
    calculate_cashflow_kpis,
    calculate_cfo_quality_score,
    calculate_fcf_conversion,
    calculate_free_cash_flow,
    classify_capital_allocation_pattern,
)


def test_free_cash_flow_calculates_normal_and_negative_values():
    assert calculate_free_cash_flow(250, -80) == 170.0
    assert calculate_free_cash_flow(50, -120) == -70.0


@pytest.mark.parametrize(
    ("cfo", "pat", "expected_value", "expected_label"),
    [
        (150, 100, 1.5, "High Quality"),
        (75, 100, 0.75, "Moderate"),
        (40, 100, 0.4, "Accrual Risk"),
    ],
)
def test_cfo_quality_classifications(cfo, pat, expected_value, expected_label):
    result = calculate_cfo_quality_score(cfo, pat)

    assert result.value == expected_value
    assert result.label == expected_label


def test_cfo_quality_returns_pat_zero_label():
    result = calculate_cfo_quality_score(100, 0)

    assert result.value is None
    assert result.label == "PAT_ZERO"


@pytest.mark.parametrize(
    ("investing_activity", "sales", "expected_value", "expected_label"),
    [
        (-20, 1000, 2.0, "Asset Light"),
        (-50, 1000, 5.0, "Moderate"),
        (-120, 1000, 12.0, "Capital Intensive"),
    ],
)
def test_capex_intensity_classifications(
    investing_activity,
    sales,
    expected_value,
    expected_label,
):
    result = calculate_capex_intensity(investing_activity, sales)

    assert result.value == expected_value
    assert result.label == expected_label


def test_fcf_conversion_calculates_percentage():
    result = calculate_fcf_conversion(160, 200)

    assert result.value == 80.0
    assert result.label is None


def test_fcf_conversion_returns_none_for_zero_operating_profit():
    result = calculate_fcf_conversion(160, 0)

    assert result.value is None


@pytest.mark.parametrize(
    ("cfo", "cfi", "cff", "quality", "expected_label"),
    [
        (100, -50, -20, KPIValue(0.8, "Moderate"), PATTERN_REINVESTOR),
        (100, -50, -20, KPIValue(1.2, "High Quality"), PATTERN_SHAREHOLDER_RETURNS),
        (100, 50, -20, None, PATTERN_LIQUIDATING_ASSETS),
        (-100, 50, 20, None, PATTERN_DISTRESS_SIGNAL),
        (-100, -50, 20, None, PATTERN_GROWTH_FUNDED_BY_DEBT),
        (100, 50, 20, None, PATTERN_CASH_ACCUMULATOR),
        (-100, -50, -20, None, PATTERN_PRE_REVENUE),
        (100, -50, 20, None, PATTERN_MIXED),
    ],
)
def test_capital_allocation_patterns(cfo, cfi, cff, quality, expected_label):
    cfo_sign, cfi_sign, cff_sign, label = classify_capital_allocation_pattern(
        cfo,
        cfi,
        cff,
        cfo_quality_score=quality,
    )

    assert (cfo_sign, cfi_sign, cff_sign) == (
        "+" if cfo > 0 else "-",
        "+" if cfi > 0 else "-",
        "+" if cff > 0 else "-",
    )
    assert label == expected_label


def test_calculate_cashflow_kpis_returns_structured_results_and_csv(tmp_path):
    export_path = tmp_path / "nested" / "capital_allocation.csv"
    records = [
        CashFlowInput("ABC", 2020, 100, -30, -10, 100, 1000, 200),
        CashFlowInput("ABC", 2021, 150, -50, -20, 100, 1000, 250),
    ]

    report = calculate_cashflow_kpis(records, export_path=export_path)

    assert report.export_path == export_path
    assert len(report.results) == 2
    assert report.results[1].free_cash_flow == 100.0
    assert report.results[1].cfo_quality_score.value == 1.25
    assert report.results[1].capital_allocation.pattern_label == (
        PATTERN_SHAREHOLDER_RETURNS
    )

    with export_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows == [
        {
            "company_id": "ABC",
            "year": "2020",
            "cfo_sign": "+",
            "cfi_sign": "-",
            "cff_sign": "-",
            "pattern_label": PATTERN_REINVESTOR,
        },
        {
            "company_id": "ABC",
            "year": "2021",
            "cfo_sign": "+",
            "cfi_sign": "-",
            "cff_sign": "-",
            "pattern_label": PATTERN_SHAREHOLDER_RETURNS,
        },
    ]
