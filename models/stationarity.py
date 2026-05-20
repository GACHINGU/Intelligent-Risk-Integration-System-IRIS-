# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Stationarity Tests (ADF + KPSS)
#
# WHAT IS STATIONARITY? (Plain English)
# A stationary series fluctuates around a stable average over time.
# A non-stationary series drifts — it has no fixed level to return to.
#
# WHY THIS MATTERS FOR IRIS:
# Before running VECM, GARCH, or any model — we must know whether
# each series is stationary or not. If we skip this and run models
# on non-stationary data, we get confident-looking but meaningless results.
# This is the foundation check. Everything else depends on it.
#
# WE RUN TWO TESTS:
#   ADF  — null hypothesis: series IS non-stationary (unit root exists)
#   KPSS — null hypothesis: series IS stationary
# Running both gives us a cross-check. If they agree, we are confident.
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller, kpss
from utils.logger import get_logger

logger = get_logger(__name__)


def run_adf(series: pd.Series, name: str) -> dict:
    """
    Run the Augmented Dickey-Fuller test on a series.

    INPUT:
        series — pandas Series of numeric values
        name   — label for logging (e.g. 'inflation')

    OUTPUT: dict with test results and plain-English interpretation
    """
    clean = series.dropna()

    try:
        adf_stat, p_value, n_lags, n_obs, crit_vals, _ = adfuller(clean, autolag='AIC')

        # Interpret: p < 0.05 means reject H0 → series IS stationary
        is_stationary = p_value < 0.05

        result = {
            "test":          "ADF",
            "series":        name,
            "statistic":     round(adf_stat, 4),
            "p_value":       round(p_value, 4),
            "n_lags":        n_lags,
            "n_obs":         n_obs,
            "crit_1pct":     round(crit_vals["1%"], 4),
            "crit_5pct":     round(crit_vals["5%"], 4),
            "crit_10pct":    round(crit_vals["10%"], 4),
            "is_stationary": is_stationary,
            "verdict":       "STATIONARY" if is_stationary else "NON-STATIONARY",
            "plain_english": (
                f"{name} is STATIONARY — it fluctuates around a stable average. "
                f"Shocks are temporary."
                if is_stationary else
                f"{name} is NON-STATIONARY — it drifts without a fixed average. "
                f"Shocks may be permanent."
            ),
        }

        logger.info(f"ADF [{name}]: stat={adf_stat:.4f}, p={p_value:.4f} → {result['verdict']}")
        return result

    except Exception as e:
        logger.error(f"ADF test failed for {name}: {e}")
        return {"test": "ADF", "series": name, "error": str(e), "is_stationary": None}


def run_kpss(series: pd.Series, name: str) -> dict:
    """
    Run the KPSS test on a series.

    INPUT:
        series — pandas Series of numeric values
        name   — label for logging

    OUTPUT: dict with test results and plain-English interpretation
    """
    clean = series.dropna()

    try:
        kpss_stat, p_value, n_lags, crit_vals = kpss(clean, regression='c', nlags='auto')

        # Interpret: p < 0.05 means reject H0 → series IS non-stationary
        is_stationary = p_value >= 0.05

        result = {
            "test":          "KPSS",
            "series":        name,
            "statistic":     round(kpss_stat, 4),
            "p_value":       round(p_value, 4),
            "n_lags":        n_lags,
            "crit_1pct":     round(crit_vals["1%"], 4),
            "crit_5pct":     round(crit_vals["5%"], 4),
            "crit_10pct":    round(crit_vals["10%"], 4),
            "is_stationary": is_stationary,
            "verdict":       "STATIONARY" if is_stationary else "NON-STATIONARY",
            "plain_english": (
                f"{name} is STATIONARY — consistent with a stable long-run mean."
                if is_stationary else
                f"{name} is NON-STATIONARY — no stable long-run mean detected."
            ),
        }

        logger.info(f"KPSS [{name}]: stat={kpss_stat:.4f}, p={p_value:.4f} → {result['verdict']}")
        return result

    except Exception as e:
        logger.error(f"KPSS test failed for {name}: {e}")
        return {"test": "KPSS", "series": name, "error": str(e), "is_stationary": None}


def run_stationarity(series: pd.Series, name: str) -> dict:
    """
    Run both ADF and KPSS tests and produce a combined verdict.

    INPUT:
        series — pandas Series
        name   — series label

    OUTPUT: dict with both test results and a combined verdict
    """
    adf_result  = run_adf(series, name)
    kpss_result = run_kpss(series, name)

    adf_stat  = adf_result.get("is_stationary")
    kpss_stat = kpss_result.get("is_stationary")

    # Combined verdict logic
    if adf_stat is True and kpss_stat is True:
        combined       = "STATIONARY"
        integration    = "I(0)"
        confidence     = "HIGH"
        recommendation = "Use series in levels. No differencing needed."
    elif adf_stat is False and kpss_stat is False:
        combined       = "NON-STATIONARY"
        integration    = "I(1) likely"
        confidence     = "HIGH"
        recommendation = "Difference the series once before modelling."
    else:
        combined       = "UNCERTAIN"
        integration    = "Unknown"
        confidence     = "LOW"
        recommendation = "Results conflict. Treat with caution. May be near-unit-root."

    return {
        "series":         name,
        "adf":            adf_result,
        "kpss":           kpss_result,
        "combined":       combined,
        "integration":    integration,
        "confidence":     confidence,
        "recommendation": recommendation,
    }


def run_all_stationarity(df: pd.DataFrame) -> dict:
    """
    Run stationarity tests on both interest_rate and inflation.
    Also tests their first differences (year-on-year changes).

    INPUT:  df — combined annual DataFrame with interest_rate and inflation
    OUTPUT: dict with results for all series tested
    """
    logger.info("Running stationarity tests on all series...")

    results = {}

    for col in ["interest_rate", "inflation"]:
        if col not in df.columns:
            logger.warning(f"Column {col} not found. Skipping stationarity test.")
            continue

        # Test the level (original series)
        results[col] = run_stationarity(df[col], col)

        # Test the first difference (year-on-year change)
        diff_series = df[col].diff().dropna()
        results[f"{col}_diff"] = run_stationarity(diff_series, f"{col} (first difference)")

    logger.info("Stationarity tests complete.")
    return results