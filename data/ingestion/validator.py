# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Data Validator
#
# WHY VALIDATION?
# Before we pass any data to the statistical models, we must verify it is
# clean, complete, and makes economic sense.
# A model fed bad data will produce confident-looking but wrong results.
# Garbage in = garbage out — especially dangerous in a risk system.
#
# This module checks:
#   1. The data is not empty
#   2. Required columns exist
#   3. Values are within economically plausible ranges
#   4. There are no extreme outliers that suggest data errors
#   5. The series has enough observations for the models to run
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Plausible value ranges (economic sanity checks) ───────────────────────────
# If a value is outside these ranges, it is likely a data error
PLAUSIBLE_RANGES = {
    "inflation":     (-10.0, 200.0),   # -10% to 200% (very generous upper bound)
    "interest_rate": (-20.0, 100.0),   # -20% to 100%
}

# Minimum observations needed for models to produce reliable results
MIN_OBSERVATIONS = 20


class ValidationResult:
    """
    Holds the result of a validation check.
    Makes it easy to pass results around and display them in the dashboard.
    """
    def __init__(self, passed: bool, warnings: list, errors: list):
        self.passed   = passed      # True if data is usable
        self.warnings = warnings    # Non-fatal issues (data still usable)
        self.errors   = errors      # Fatal issues (data should not be used)

    def __repr__(self):
        status = "PASSED" if self.passed else "FAILED"
        return (f"ValidationResult({status}, "
                f"{len(self.warnings)} warnings, "
                f"{len(self.errors)} errors)")


def validate_dataframe(df: pd.DataFrame, series_name: str) -> ValidationResult:
    """
    Run all validation checks on a single time series DataFrame.

    INPUT:
        df          — DataFrame with at least columns: date, value
        series_name — 'inflation' or 'interest_rate'

    OUTPUT:
        ValidationResult object
    """
    warnings = []
    errors   = []

    # ── Check 1: Not empty ────────────────────────────────────────────────────
    if df is None or df.empty:
        errors.append(f"{series_name}: DataFrame is empty or None.")
        return ValidationResult(False, warnings, errors)

    # ── Check 2: Required columns exist ──────────────────────────────────────
    required_cols = ["date", "value"]
    missing_cols  = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        errors.append(f"{series_name}: Missing columns: {missing_cols}")
        return ValidationResult(False, warnings, errors)

    # ── Check 3: Minimum observations ─────────────────────────────────────────
    n_obs = len(df.dropna(subset=["value"]))
    if n_obs < MIN_OBSERVATIONS:
        errors.append(
            f"{series_name}: Only {n_obs} valid observations. "
            f"Minimum required: {MIN_OBSERVATIONS}."
        )
        return ValidationResult(False, warnings, errors)

    # ── Check 4: Value range check ────────────────────────────────────────────
    low, high = PLAUSIBLE_RANGES.get(series_name, (-1000, 1000))
    out_of_range = df[(df["value"] < low) | (df["value"] > high)]
    if not out_of_range.empty:
        warnings.append(
            f"{series_name}: {len(out_of_range)} values outside plausible range "
            f"({low}% to {high}%). Dates: {out_of_range['date'].tolist()}"
        )

    # ── Check 5: Missing values ───────────────────────────────────────────────
    n_missing = df["value"].isna().sum()
    if n_missing > 0:
        pct_missing = (n_missing / len(df)) * 100
        if pct_missing > 20:
            errors.append(
                f"{series_name}: {pct_missing:.1f}% of values are missing. "
                f"Too many gaps for reliable modelling."
            )
        else:
            warnings.append(
                f"{series_name}: {n_missing} missing values ({pct_missing:.1f}%). "
                f"Will be handled in cleaning step."
            )

    # ── Check 6: Date column is parseable ────────────────────────────────────
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        try:
            pd.to_datetime(df["date"])
            warnings.append(f"{series_name}: Date column is not datetime type — will be converted.")
        except Exception:
            errors.append(f"{series_name}: Date column cannot be parsed as dates.")
            return ValidationResult(False, warnings, errors)

    # ── Check 7: Extreme single-period spike (likely data error) ──────────────
    values      = df["value"].dropna()
    if len(values) > 5:
        pct_changes = values.pct_change().abs()
        extreme     = pct_changes[pct_changes > 5.0]    # > 500% change in one period
        if not extreme.empty:
            warnings.append(
                f"{series_name}: {len(extreme)} extreme period-on-period changes detected. "
                f"Possible data errors — review carefully."
            )

    # ── Check 8: Latest value freshness ──────────────────────────────────────
    if pd.api.types.is_datetime64_any_dtype(df["date"]):
        latest_date = df["date"].max()
        days_old    = (pd.Timestamp.now() - latest_date).days
        if days_old > 180:
            warnings.append(
                f"{series_name}: Latest data point is {days_old} days old "
                f"({latest_date.strftime('%Y-%m-%d')}). May not reflect current conditions."
            )

    # ── Final result ──────────────────────────────────────────────────────────
    passed = len(errors) == 0

    if passed:
        logger.info(f"Validation PASSED for {series_name}. "
                    f"{n_obs} observations. {len(warnings)} warnings.")
    else:
        logger.error(f"Validation FAILED for {series_name}. "
                     f"Errors: {errors}")

    return ValidationResult(passed, warnings, errors)


def validate_all(live_data: dict) -> dict:
    """
    Validate all series in the live data dict.

    INPUT:  live_data — dict from fetch_all_kenya_indicators() or cache
    OUTPUT: dict with validation results for each series
    """
    results = {}

    for series_name in ["inflation", "interest_rate"]:
        df = live_data.get(series_name, pd.DataFrame())
        results[series_name] = validate_dataframe(df, series_name)

    # Overall system validation
    all_passed = all(r.passed for r in results.values())
    results["overall_passed"] = all_passed

    if all_passed:
        logger.info("All data validation checks passed.")
    else:
        failed = [k for k, v in results.items()
                  if k != "overall_passed" and hasattr(v, "passed") and not v.passed]
        logger.warning(f"Validation failed for: {failed}")

    return results