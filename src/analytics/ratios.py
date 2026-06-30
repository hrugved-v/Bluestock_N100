"""Financial ratio engine.

This module contains pure, typed calculation helpers for profitability,
leverage and efficiency ratios. It does not mutate Sprint 1 loaders, schema or
database state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

PERCENT_MULTIPLIER = 100.0
ROUND_DIGITS = 2
FINANCIAL_SECTOR_TERMS = (
    "bank",
    "finance",
    "financial",
    "insurance",
    "nbfc",
    "asset management",
    "capital market",
)


@dataclass(frozen=True)
class RatioResult:
    """Structured ratio output with optional labels and warning indicators."""

    value: Optional[float]
    flag: Optional[str] = None
    explanation: Optional[str] = None
    label: Optional[str] = None
    high_leverage_flag: bool = False
    interest_coverage_warning: bool = False

    def as_dict(self) -> dict[str, Optional[float] | Optional[str] | bool]:
        """Return a serialisable representation for callers and tests."""
        return {
            "value": self.value,
            "flag": self.flag,
            "explanation": self.explanation,
            "label": self.label,
            "high_leverage_flag": self.high_leverage_flag,
            "interest_coverage_warning": self.interest_coverage_warning,
        }


@dataclass(frozen=True)
class RatioInputs:
    """Annual statement values needed by the Day 8 ratio engine."""

    sales: Optional[float] = None
    operating_profit: Optional[float] = None
    other_income: Optional[float] = None
    net_profit: Optional[float] = None
    profit_before_tax: Optional[float] = None
    interest: Optional[float] = None
    equity_capital: Optional[float] = None
    reserves: Optional[float] = None
    borrowings: Optional[float] = None
    investments: Optional[float] = None
    total_assets: Optional[float] = None
    broad_sector: Optional[str] = None
    sub_sector: Optional[str] = None


def _round(value: float) -> float:
    return round(value, ROUND_DIGITS)


def _has_missing(*values: Optional[float]) -> bool:
    return any(value is None for value in values)


def _result(
    value: Optional[float],
    flag: Optional[str] = None,
    explanation: Optional[str] = None,
    label: Optional[str] = None,
    high_leverage_flag: bool = False,
    interest_coverage_warning: bool = False,
) -> RatioResult:
    rounded_value = _round(value) if value is not None else None
    return RatioResult(
        rounded_value,
        flag,
        explanation,
        label,
        high_leverage_flag,
        interest_coverage_warning,
    )


def is_financial_sector(
    broad_sector: Optional[str],
    sub_sector: Optional[str] = None,
) -> bool:
    """Return True for banks, insurers, NBFCs and related finance firms."""
    sector_text = f"{broad_sector or ''} {sub_sector or ''}".lower()
    return any(term in sector_text for term in FINANCIAL_SECTOR_TERMS)


def shareholder_equity(
    equity_capital: Optional[float],
    reserves: Optional[float],
) -> Optional[float]:
    """Calculate shareholder equity from balance-sheet components."""
    if _has_missing(equity_capital, reserves):
        return None
    return float(equity_capital) + float(reserves)


def safe_divide(
    numerator: Optional[float],
    denominator: Optional[float],
    *,
    multiplier: float = 1.0,
    metric_name: str,
) -> RatioResult:
    """Divide two numbers and convert invalid cases into warning flags."""
    if _has_missing(numerator, denominator):
        return _result(
            None,
            "missing_input",
            f"{metric_name} cannot be calculated because an input is missing.",
        )
    if denominator == 0:
        return _result(
            None,
            "zero_denominator",
            f"{metric_name} cannot be calculated with a zero denominator.",
        )
    return _result((float(numerator) / float(denominator)) * multiplier)


def net_profit_margin(
    net_profit: Optional[float],
    sales: Optional[float],
) -> RatioResult:
    """Calculate net profit margin percentage."""
    return safe_divide(
        net_profit,
        sales,
        multiplier=PERCENT_MULTIPLIER,
        metric_name="net profit margin",
    )


def operating_profit_margin(
    operating_profit: Optional[float],
    sales: Optional[float],
) -> RatioResult:
    """Calculate operating profit margin percentage."""
    return safe_divide(
        operating_profit,
        sales,
        multiplier=PERCENT_MULTIPLIER,
        metric_name="operating profit margin",
    )


def return_on_equity(
    net_profit: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
) -> RatioResult:
    """Calculate return on equity percentage."""
    equity = shareholder_equity(equity_capital, reserves)
    if equity is not None and equity < 0:
        return _result(
            None,
            "negative_equity",
            "ROE is not meaningful when shareholder equity is negative.",
        )
    return safe_divide(
        net_profit,
        equity,
        multiplier=PERCENT_MULTIPLIER,
        metric_name="return on equity",
    )


def return_on_capital_employed(
    profit_before_tax: Optional[float],
    interest: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    borrowings: Optional[float],
    *,
    financial_sector: bool = False,
) -> RatioResult:
    """Calculate ROCE as EBIT divided by capital employed."""
    if financial_sector:
        return _result(
            None,
            "financial_sector_not_applicable",
            "ROCE is skipped for financial-sector companies.",
        )

    equity = shareholder_equity(equity_capital, reserves)
    if _has_missing(profit_before_tax, interest, equity, borrowings):
        return _result(
            None,
            "missing_input",
            "ROCE cannot be calculated because an input is missing.",
        )

    capital_employed = float(equity) + float(borrowings)
    if capital_employed <= 0:
        return _result(
            None,
            "non_positive_capital_employed",
            "ROCE is not meaningful with non-positive capital employed.",
        )

    ebit = float(profit_before_tax) + float(interest)
    return _result((ebit / capital_employed) * PERCENT_MULTIPLIER)


def return_on_assets(
    net_profit: Optional[float],
    total_assets: Optional[float],
) -> RatioResult:
    """Calculate return on assets percentage."""
    return safe_divide(
        net_profit,
        total_assets,
        multiplier=PERCENT_MULTIPLIER,
        metric_name="return on assets",
    )


def debt_to_equity(
    borrowings: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    *,
    broad_sector: Optional[str] = None,
    financial_sector: bool = False,
) -> RatioResult:
    """Calculate debt-to-equity and flag highly levered non-financial firms."""
    equity = shareholder_equity(equity_capital, reserves)
    if borrowings == 0:
        return _result(0.0, "debt_free", "Company has no borrowings.")
    if _has_missing(borrowings, equity):
        return _result(
            None,
            "missing_input",
            "Debt-to-equity cannot be calculated because an input is missing.",
        )
    if equity <= 0:
        return _result(
            None,
            "non_positive_equity",
            "Debt-to-equity is not meaningful with non-positive equity.",
        )

    value = float(borrowings) / float(equity)
    high_leverage_flag = (
        value > 5
        and not financial_sector
        and (broad_sector or "").strip().lower() != "financials"
    )
    return _result(value, high_leverage_flag=high_leverage_flag)


def interest_coverage(
    operating_profit: Optional[float],
    interest: Optional[float],
    other_income: Optional[float] = 0,
    borrowings: Optional[float] = None,
    *,
    financial_sector: bool = False,
) -> RatioResult:
    """Calculate interest coverage as operating profit plus other income over interest."""
    if financial_sector:
        return _result(
            None,
            "financial_sector_not_applicable",
            "Interest coverage is skipped for financial-sector companies.",
        )
    if _has_missing(operating_profit, other_income, interest):
        return _result(
            None,
            "missing_input",
            "Interest coverage cannot be calculated because an input is missing.",
        )
    if interest == 0:
        return _result(
            None,
            "debt_free" if borrowings == 0 else "no_interest_expense",
            "Interest expense is zero.",
            label="Debt Free",
        )

    value = (float(operating_profit) + float(other_income)) / float(interest)
    return _result(value, interest_coverage_warning=value < 1.5)


def net_debt(
    borrowings: Optional[float],
    investments: Optional[float],
    *,
    financial_sector: bool = False,
) -> RatioResult:
    """Estimate net debt as borrowings less investments/cash-like assets."""
    if _has_missing(borrowings, investments):
        return _result(
            None,
            "missing_input",
            "Net debt cannot be calculated because an input is missing.",
        )
    return _result(float(borrowings) - float(investments))


def asset_turnover(
    sales: Optional[float],
    total_assets: Optional[float],
    *,
    financial_sector: bool = False,
) -> RatioResult:
    """Calculate asset turnover."""
    return safe_divide(
        sales,
        total_assets,
        metric_name="asset turnover",
    )


def calculate_all_ratios(inputs: RatioInputs) -> dict[str, RatioResult]:
    """Calculate financial ratios for one company-year."""
    financial_sector = is_financial_sector(inputs.broad_sector, inputs.sub_sector)
    return {
        "net_profit_margin_pct": net_profit_margin(
            inputs.net_profit,
            inputs.sales,
        ),
        "operating_profit_margin_pct": operating_profit_margin(
            inputs.operating_profit,
            inputs.sales,
        ),
        "return_on_equity_pct": return_on_equity(
            inputs.net_profit,
            inputs.equity_capital,
            inputs.reserves,
        ),
        "roce_pct": return_on_capital_employed(
            inputs.profit_before_tax,
            inputs.interest,
            inputs.equity_capital,
            inputs.reserves,
            inputs.borrowings,
            financial_sector=financial_sector,
        ),
        "return_on_assets_pct": return_on_assets(
            inputs.net_profit,
            inputs.total_assets,
        ),
        "debt_to_equity": debt_to_equity(
            inputs.borrowings,
            inputs.equity_capital,
            inputs.reserves,
            broad_sector=inputs.broad_sector,
            financial_sector=financial_sector,
        ),
        "interest_coverage": interest_coverage(
            inputs.operating_profit,
            inputs.interest,
            inputs.other_income,
            inputs.borrowings,
            financial_sector=financial_sector,
        ),
        "net_debt_cr": net_debt(
            inputs.borrowings,
            inputs.investments,
            financial_sector=financial_sector,
        ),
        "asset_turnover": asset_turnover(
            inputs.sales,
            inputs.total_assets,
            financial_sector=financial_sector,
        ),
    }
