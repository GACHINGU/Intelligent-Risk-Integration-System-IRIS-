# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Data Cleaner
#
# Takes raw data from the API (or cache) and produces clean,
# model-ready DataFrames.
#
# Steps:
#   1. Parse and standardise date formats
#   2. Remove duplicate dates (keep most recent)
#   3. Fill small gaps using forward-fill (carry last known value forward)
#   4. Remove extreme outliers that are clearly data errors
#   5. Standardise column names across both series
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)


def clean_series(df: pd.DataFrame, series_name: str) -> pd.DataFrame:
    """
    Clean a single time series DataFrame.

    INPUT:
        df          — raw DataFrame with columns: date, value
        series_name — 'inflation' or 'interest_rate' (used for logging)

    OUTPUT:
        Clean DataFrame with columns: date, value, year, month
    """
    if df is None or df.empty:
        logger.warning(f"Cannot clean {series_name}: empty DataFrame.")
        return pd.DataFrame()

    df = df.copy()

    # ── Step 1: Parse dates ───────────────────────────────────────────────────
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    before = len(df)
    df     = df.dropna(subset=["date"])
    if len(df) < before:
        logger.warning(f"{series_name}: Dropped {before - len(df)} rows with unparseable dates.")

    # ── Step 2: Parse values ──────────────────────────────────────────────────
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    before = len(df)
    df     = df.dropna(subset=["value"])
    if len(df) < before:
        logger.warning(f"{series_name}: Dropped {before - len(df)} rows with non-numeric values.")

    # ── Step 3: Remove duplicates (keep last reading per date) ────────────────
    before = len(df)
    df     = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    if len(df) < before:
        logger.info(f"{series_name}: Removed {before - len(df)} duplicate date entries.")

    # ── Step 4: Sort chronologically ──────────────────────────────────────────
    df = df.sort_values("date").reset_index(drop=True)

    # ── Step 5: Add year and month columns (useful for models and charts) ─────
    df["year"]  = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # ── Step 6: Forward-fill small gaps (up to 3 consecutive missing periods) ─
    # We do NOT interpolate — we carry the last known value forward
    # This is standard practice for policy rate data (rates don't change monthly)
    df = df.set_index("date")
    df["value"] = df["value"].fillna(method="ffill", limit=3)
    df = df.reset_index()

    # ── Step 7: Rename value column to series-specific name ───────────────────
    df = df.rename(columns={"value": series_name})

    # ── Final column selection ────────────────────────────────────────────────
    df = df[["date", "year", "month", series_name]].copy()

    logger.info(f"{series_name}: Cleaned. {len(df)} observations. "
                f"Range: {df['date'].min().strftime('%Y-%m')} to {df['date'].max().strftime('%Y-%m')}")

    return df


def clean_all(live_data: dict) -> dict:
    """
    Clean all series from the live data fetch result.

    INPUT:  live_data — dict from fetch_all_kenya_indicators()
    OUTPUT: dict with cleaned DataFrames for each series
    """
    logger.info("Starting data cleaning pipeline...")

    cleaned = {
        "inflation":     clean_series(live_data.get("inflation",     pd.DataFrame()), "inflation"),
        "interest_rate": clean_series(live_data.get("interest_rate", pd.DataFrame()), "interest_rate"),
        "latest":        live_data.get("latest", {}),
        "fetch_time":    live_data.get("fetch_time"),
        "success":       live_data.get("success", False),
    }

    logger.info("Data cleaning complete.")
    return cleaned