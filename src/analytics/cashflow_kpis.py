"""Cash-flow KPI engine for Sprint 2 Day 11.

This module keeps cash-flow analytics separate from persistence. It calculates
structured KPI results and can export the requested capital-allocation pattern
CSV, but it does not write to SQLite or mutate upstream data sources.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PERCENT_MULTIPLIER = 100.0
ROUND_DIGITS = 2
DEFAULT_ROLLING_YEARS = 5
DEFAULT_EXPORT_PATH = Path("output/capital_allocation.csv")

LABEL_HIGH_QUALITY = "High Quality"
LABEL_MODERATE = "Moderate"
LABEL_ACCRUAL_RISK = "Accrual Risk"
LABEL_PAT_ZERO = "PAT_ZERO"
LABEL_ASSET_LIGHT = "Asset Light"
LABEL_CAPEX_MODERATE = "Moderate"
LABEL_CAPITAL_INTENSIVE = "Capital Intensive"

SIGN_POSITIVE = "+"
SIGN_NEGATIVE = "-"
SIGN_ZERO = "0"

PATTERN_REINVESTOR = "Reinvestor"
PATTERN_SHAREHOLDER_RETURNS = "Shareholder Returns"
PATTERN_LIQUIDATING_ASSETS = "Liquidating Assets"
PATTERN_DISTRESS_SIGNAL = "Distress Signal"
PATTERN_GROWTH_FUNDED_BY_DEBT = "Growth Funded by Debt"
PATTERN_CASH_ACCUMULATOR = "Cash Accumulator"
PATTERN_PRE_REVENUE = "Pre-Revenue"
PATTERN_MIXED = "Mixed"

_PATTERN_LABELS = {
    (SIGN_POSITIVE, SIGN_POSITIVE, SIGN_NEGATIVE): PATTERN_LIQUIDATING_ASSETS,
    (SIGN_NEGATIVE, SIGN_POSITIVE, SIGN_POSITIVE): PATTERN_DISTRESS_SIGNAL,
    (SIGN_NEGATIVE, SIGN_NEGATIVE, SIGN_POSITIVE): PATTERN_GROWTH_FUNDED_BY_DEBT,
    (SIGN_POSITIVE, SIGN_POSITIVE, SIGN_POSITIVE): PATTERN_CASH_ACCUMULATOR,
    (SIGN_NEGATIVE, SIGN_NEGATIVE, SIGN_NEGATIVE): PATTERN_PRE_REVENUE,
    (SIGN_POSITIVE, SIGN_NEGATIVE, SIGN_POSITIVE): PATTERN_MIXED,
}

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CashFlowInput:
    """Annual cash-flow and income-statement values for one company-year."""

    company_id: str
    year: int
    operating_activity: float
    investing_activity: float
    financing_activity: float
    pat: float
    sales: float
    operating_profit: float


@dataclass(frozen=True)
class KPIValue:
    """A numeric KPI value with an optional classification label."""

    value: float | None
    label: str | None = None


@dataclass(frozen=True)
class CapitalAllocationPattern:
    """Capital-allocation classification from CFO, CFI and CFF signs."""

    company_id: str
    year: int
    cfo_sign: str
    cfi_sign: str
    cff_sign: str
    pattern_label: str

    def as_csv_row(self) -> dict[str, int | str]:
        """Return the export row expected by ``capital_allocation.csv``."""

        return {
            "company_id": self.company_id,
            "year": self.year,
            "cfo_sign": self.cfo_sign,
            "cfi_sign": self.cfi_sign,
            "cff_sign": self.cff_sign,
            "pattern_label": self.pattern_label,
        }


@dataclass(frozen=True)
class CashFlowKPIResult:
    """Calculated Day 11 cash-flow KPI result for one company-year."""

    company_id: str
    year: int
    free_cash_flow: float
    cfo_quality_score: KPIValue
    capex_intensity: KPIValue
    fcf_conversion: KPIValue
    capital_allocation: CapitalAllocationPattern


@dataclass(frozen=True)
class CashFlowKPIReport:
    """Structured output from ``calculate_cashflow_kpis``."""

    results: tuple[CashFlowKPIResult, ...]
    export_path: Path | None = None


def calculate_free_cash_flow(
    operating_activity: float | int,
    investing_activity: float | int,
) -> float:
    """Calculate free cash flow as CFO plus CFI."""

    return _round(float(operating_activity) + float(investing_activity))


def calculate_cfo_quality_score(
    operating_activity: float | int,
    pat: float | int,
) -> KPIValue:
    """Calculate and classify CFO/PAT for a single period."""

    if pat == 0:
        logger.info("CFO quality skipped because PAT is zero.")
        return KPIValue(None, LABEL_PAT_ZERO)

    value = float(operating_activity) / float(pat)
    return KPIValue(_round(value), _classify_cfo_quality(value))


def calculate_rolling_cfo_quality_score(
    records: Sequence[CashFlowInput],
) -> KPIValue:
    """Calculate the average CFO/PAT over a trailing record window."""

    if not records:
        logger.info("CFO quality skipped because no records were provided.")
        return KPIValue(None, None)

    ratios: list[float] = []
    for record in records:
        if record.pat == 0:
            logger.info(
                "CFO quality skipped for %s %s because PAT is zero.",
                record.company_id,
                record.year,
            )
            return KPIValue(None, LABEL_PAT_ZERO)
        ratios.append(float(record.operating_activity) / float(record.pat))

    value = sum(ratios) / len(ratios)
    return KPIValue(_round(value), _classify_cfo_quality(value))


def calculate_capex_intensity(
    investing_activity: float | int,
    sales: float | int,
) -> KPIValue:
    """Calculate and classify CapEx intensity as abs(CFI) over sales."""

    if sales == 0:
        logger.info("CapEx intensity skipped because sales is zero.")
        return KPIValue(None, None)

    value = abs(float(investing_activity)) / float(sales) * PERCENT_MULTIPLIER
    return KPIValue(_round(value), _classify_capex_intensity(value))


def calculate_fcf_conversion(
    free_cash_flow: float | int,
    operating_profit: float | int,
) -> KPIValue:
    """Calculate FCF conversion as FCF over operating profit."""

    if operating_profit == 0:
        logger.info("FCF conversion skipped because operating profit is zero.")
        return KPIValue(None, None)

    value = float(free_cash_flow) / float(operating_profit) * PERCENT_MULTIPLIER
    return KPIValue(_round(value), None)


def classify_capital_allocation_pattern(
    operating_activity: float | int,
    investing_activity: float | int,
    financing_activity: float | int,
    *,
    cfo_quality_score: KPIValue | None = None,
) -> tuple[str, str, str, str]:
    """Classify capital-allocation behavior from CFO, CFI and CFF signs."""

    signs = (
        _sign(operating_activity),
        _sign(investing_activity),
        _sign(financing_activity),
    )
    if signs == (SIGN_POSITIVE, SIGN_NEGATIVE, SIGN_NEGATIVE):
        label = (
            PATTERN_SHAREHOLDER_RETURNS
            if _is_high_quality(cfo_quality_score)
            else PATTERN_REINVESTOR
        )
    else:
        label = _PATTERN_LABELS.get(signs, PATTERN_MIXED)

    return signs[0], signs[1], signs[2], label


def calculate_cashflow_kpis(
    records: Sequence[CashFlowInput | Mapping[str, object]],
    *,
    rolling_years: int = DEFAULT_ROLLING_YEARS,
    export_path: str | Path | None = DEFAULT_EXPORT_PATH,
) -> CashFlowKPIReport:
    """Calculate Day 11 cash-flow KPIs for one or more annual records."""

    inputs = _sort_records(_coerce_record(record) for record in records)
    results: list[CashFlowKPIResult] = []

    for company_records in _group_by_company(inputs).values():
        for index, record in enumerate(company_records):
            window = company_records[max(0, index - rolling_years + 1): index + 1]
            results.append(_calculate_record_kpis(record, window))

    written_path = None
    if export_path is not None:
        written_path = export_capital_allocation_csv(
            [result.capital_allocation for result in results],
            export_path,
        )

    return CashFlowKPIReport(tuple(results), written_path)


def export_capital_allocation_csv(
    patterns: Sequence[CapitalAllocationPattern],
    export_path: str | Path = DEFAULT_EXPORT_PATH,
) -> Path:
    """Write capital-allocation signs and labels to a CSV file."""

    path = Path(export_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "company_id",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label",
    ]
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(pattern.as_csv_row() for pattern in patterns)

    logger.info("Capital allocation CSV exported to %s.", path)
    return path


def _calculate_record_kpis(
    record: CashFlowInput,
    quality_window: Sequence[CashFlowInput],
) -> CashFlowKPIResult:
    free_cash_flow = calculate_free_cash_flow(
        record.operating_activity,
        record.investing_activity,
    )
    cfo_quality = calculate_rolling_cfo_quality_score(quality_window)
    signs = classify_capital_allocation_pattern(
        record.operating_activity,
        record.investing_activity,
        record.financing_activity,
        cfo_quality_score=cfo_quality,
    )

    return CashFlowKPIResult(
        company_id=record.company_id,
        year=record.year,
        free_cash_flow=free_cash_flow,
        cfo_quality_score=cfo_quality,
        capex_intensity=calculate_capex_intensity(
            record.investing_activity,
            record.sales,
        ),
        fcf_conversion=calculate_fcf_conversion(
            free_cash_flow,
            record.operating_profit,
        ),
        capital_allocation=CapitalAllocationPattern(
            company_id=record.company_id,
            year=record.year,
            cfo_sign=signs[0],
            cfi_sign=signs[1],
            cff_sign=signs[2],
            pattern_label=signs[3],
        ),
    )


def _classify_cfo_quality(value: float) -> str:
    if value > 1.0:
        return LABEL_HIGH_QUALITY
    if value >= 0.5:
        return LABEL_MODERATE
    return LABEL_ACCRUAL_RISK


def _classify_capex_intensity(value: float) -> str:
    if value < 3.0:
        return LABEL_ASSET_LIGHT
    if value <= 8.0:
        return LABEL_CAPEX_MODERATE
    return LABEL_CAPITAL_INTENSIVE


def _coerce_record(record: CashFlowInput | Mapping[str, object]) -> CashFlowInput:
    if isinstance(record, CashFlowInput):
        return record

    return CashFlowInput(
        company_id=str(record["company_id"]),
        year=int(record["year"]),
        operating_activity=float(record["operating_activity"]),
        investing_activity=float(record["investing_activity"]),
        financing_activity=float(record["financing_activity"]),
        pat=float(record["pat"]),
        sales=float(record["sales"]),
        operating_profit=float(record["operating_profit"]),
    )


def _group_by_company(
    records: Sequence[CashFlowInput],
) -> dict[str, list[CashFlowInput]]:
    grouped: dict[str, list[CashFlowInput]] = {}
    for record in records:
        grouped.setdefault(record.company_id, []).append(record)
    return grouped


def _sort_records(records: Sequence[CashFlowInput]) -> list[CashFlowInput]:
    return sorted(records, key=lambda record: (record.company_id, record.year))


def _sign(value: float | int) -> str:
    if value > 0:
        return SIGN_POSITIVE
    if value < 0:
        return SIGN_NEGATIVE
    return SIGN_ZERO


def _is_high_quality(score: KPIValue | None) -> bool:
    return score is not None and score.value is not None and score.value > 1.0


def _round(value: float) -> float:
    return round(value, ROUND_DIGITS)
