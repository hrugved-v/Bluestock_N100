"""Generic CAGR engine for yearly financial observations.

The module intentionally keeps CAGR calculation metric-agnostic. Revenue,
PAT, EPS and future annual measures can all reuse the same validated
calculation path without duplicating financial-specific functions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping, Sequence

PERCENT_MULTIPLIER = 100.0
ROUND_DIGITS = 2
SUPPORTED_WINDOWS = (3, 5, 10)

FLAG_DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
FLAG_TURNAROUND = "TURNAROUND"
FLAG_BOTH_NEGATIVE = "BOTH_NEGATIVE"
FLAG_ZERO_BASE = "ZERO_BASE"
FLAG_INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CAGRResult:
    """Structured CAGR output.

    Attributes:
        value: CAGR percentage rounded to two decimals, or None when the
            calculation is not meaningful.
        flag: A machine-readable reason when CAGR cannot be calculated.
    """

    value: float | None
    flag: str | None = None


@dataclass(frozen=True)
class YearlyValue:
    """A generic annual observation used by the CAGR window calculator."""

    year: int
    value: float | None


def calculate_cagr(
    beginning_value: float | int | None,
    ending_value: float | int | None,
    years: int,
) -> CAGRResult:
    """Calculate CAGR percentage for a beginning and ending value.

    The function implements the standard CAGR formula and centralises all
    edge-case flags so every metric receives identical treatment.
    """

    if years <= 0 or beginning_value is None or ending_value is None:
        logger.info("CAGR skipped because the year window or values are missing.")
        return CAGRResult(None, FLAG_INSUFFICIENT_HISTORY)

    beginning = float(beginning_value)
    ending = float(ending_value)

    if beginning == 0:
        logger.info("CAGR skipped because the base value is zero.")
        return CAGRResult(None, FLAG_ZERO_BASE)
    if beginning > 0 and ending < 0:
        logger.info("CAGR skipped because the metric declined from profit to loss.")
        return CAGRResult(None, FLAG_DECLINE_TO_LOSS)
    if beginning < 0 and ending > 0:
        logger.info("CAGR skipped because the metric turned around from loss.")
        return CAGRResult(None, FLAG_TURNAROUND)
    if beginning < 0 and ending < 0:
        logger.info("CAGR skipped because both values are negative.")
        return CAGRResult(None, FLAG_BOTH_NEGATIVE)
    if beginning < 0 or ending < 0:
        logger.info("CAGR skipped because a negative value makes CAGR ambiguous.")
        return CAGRResult(None, FLAG_INSUFFICIENT_HISTORY)

    value = ((ending / beginning) ** (1 / years) - 1) * PERCENT_MULTIPLIER
    return CAGRResult(round(value, ROUND_DIGITS), None)


class CAGRCalculator:
    """Generic calculator for fixed-year CAGR windows.

    The calculator accepts generic yearly observations and does not know
    whether the values represent revenue, PAT, EPS or another annual metric.
    """

    supported_windows: tuple[int, ...] = SUPPORTED_WINDOWS

    def calculate_cagr(
        self,
        beginning_value: float | int | None,
        ending_value: float | int | None,
        years: int,
    ) -> CAGRResult:
        """Calculate CAGR for explicit beginning and ending values."""

        return calculate_cagr(beginning_value, ending_value, years)

    def calculate_for_window(
        self,
        records: Sequence[YearlyValue | Mapping[str, object]],
        years: int,
        *,
        year_key: str = "year",
        value_key: str = "value",
    ) -> CAGRResult:
        """Calculate CAGR for the latest complete year window in records.

        The latest observation is used as the ending point. The beginning
        observation must exist exactly ``years`` before that ending year;
        otherwise an insufficient-history flag is returned.
        """

        if not self._is_supported_window(years):
            logger.info("Unsupported CAGR window requested: %s", years)
            return CAGRResult(None, FLAG_INSUFFICIENT_HISTORY)

        observations = self._sort_yearly_records(records, year_key, value_key)
        pair = self._locate_observation_pair(observations, years)
        if pair is None:
            logger.info("CAGR skipped because no complete %s-year window exists.", years)
            return CAGRResult(None, FLAG_INSUFFICIENT_HISTORY)

        beginning, ending = pair
        return self.calculate_cagr(beginning.value, ending.value, years)

    def calculate_windows(
        self,
        records: Sequence[YearlyValue | Mapping[str, object]],
        windows: Sequence[int] = SUPPORTED_WINDOWS,
        *,
        year_key: str = "year",
        value_key: str = "value",
    ) -> dict[int, CAGRResult]:
        """Calculate multiple CAGR windows using the same generic engine."""

        return {
            window: self.calculate_for_window(
                records,
                window,
                year_key=year_key,
                value_key=value_key,
            )
            for window in windows
        }

    def _is_supported_window(self, years: int) -> bool:
        """Return True when the requested period is a supported CAGR window."""

        return years in self.supported_windows

    def _sort_yearly_records(
        self,
        records: Sequence[YearlyValue | Mapping[str, object]],
        year_key: str,
        value_key: str,
    ) -> list[YearlyValue]:
        """Return valid yearly observations sorted from oldest to newest."""

        observations = [
            self._coerce_record(record, year_key, value_key)
            for record in records
        ]
        return sorted(observations, key=lambda record: record.year)

    def _coerce_record(
        self,
        record: YearlyValue | Mapping[str, object],
        year_key: str,
        value_key: str,
    ) -> YearlyValue:
        """Convert a supported record shape into a YearlyValue."""

        if isinstance(record, YearlyValue):
            return record

        year = record.get(year_key)
        value = record.get(value_key)
        if year is None:
            raise ValueError(f"Missing required year key: {year_key}")

        numeric_value = None if value is None else float(value)
        return YearlyValue(int(year), numeric_value)

    def _locate_observation_pair(
        self,
        observations: Sequence[YearlyValue],
        years: int,
    ) -> tuple[YearlyValue, YearlyValue] | None:
        """Locate exact start and end observations for a CAGR window."""

        if not observations:
            return None

        by_year = {observation.year: observation for observation in observations}
        ending = observations[-1]
        beginning = by_year.get(ending.year - years)
        if beginning is None:
            return None

        return beginning, ending
