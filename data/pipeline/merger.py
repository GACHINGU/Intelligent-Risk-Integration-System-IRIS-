# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Data Merger
#
# WHY MERGING?
# Our models need a long historical series to produce reliable results.
# The Trading Economics API gives us recent data (typically 2000-present).
# We have historical data going back to 1971.
#
# This module:
#   1. Loads the historical CSV baseline (1971-2023)
#   2. Appends the live API data if available
#   3. Removes duplicates (API data takes priority for overlapping dates)
#   4. Produces one unified series from 1971 to today
#
# FALLBACK BEHAVIOUR:
#   If the API is unavailable (no key, no internet, rate limit),
#   the system falls back to historical data only.
#   IRIS still runs — just without the most recent live reading.
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
import os
from config.settings import HISTORICAL_IR_PATH, HISTORICAL_INF_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


def load_historical_data() -> dict:
    """
    Load the historical CSV files that came with the project.

    OUTPUT: dict with keys 'inflation' and 'interest_rate'
            Each value is a DataFrame with columns: date, year, month, {series}
    """
    historical = {}

    # ── Load interest rates ───────────────────────────────────────────────────
    if os.path.exists(HISTORICAL_IR_PATH):
        try:
            ir_df = pd.read_csv(HISTORICAL_IR_PATH)

            # Verify it is not empty and has expected columns
            if ir_df.empty or "year" not in ir_df.columns:
                logger.error(f"Historical interest rate file exists but is empty or malformed.")
                historical["interest_rate"] = pd.DataFrame()
            else:
                ir_df = ir_df.dropna(subset=["year", "interest_rate"])
                ir_df["year"]  = ir_df["year"].astype(int)
                ir_df["date"]  = pd.to_datetime(ir_df["year"].astype(str) + "-01-01")
                ir_df["month"] = 1
                ir_df = ir_df[["date", "year", "month", "interest_rate"]].sort_values("date").reset_index(drop=True)
                historical["interest_rate"] = ir_df
                logger.info(f"Historical interest rates loaded: {len(ir_df)} observations "
                            f"({int(ir_df['year'].min())} - {int(ir_df['year'].max())})")
        except Exception as e:
            logger.error(f"Failed to load historical interest rates: {e}")
            historical["interest_rate"] = pd.DataFrame()
    else:
        logger.error(f"Historical interest rate file not found at: {HISTORICAL_IR_PATH}")
        logger.error("Please copy kenya_interest_rates.csv into data/historical/")
        historical["interest_rate"] = pd.DataFrame()

    # ── Load inflation ────────────────────────────────────────────────────────
    if os.path.exists(HISTORICAL_INF_PATH):
        try:
            inf_df = pd.read_csv(HISTORICAL_INF_PATH)

            if inf_df.empty or "year" not in inf_df.columns:
                logger.error(f"Historical inflation file exists but is empty or malformed.")
                historical["inflation"] = pd.DataFrame()
            else:
                inf_df = inf_df.dropna(subset=["year", "inflation"])
                inf_df["year"]  = inf_df["year"].astype(int)
                inf_df["date"]  = pd.to_datetime(inf_df["year"].astype(str) + "-01-01")
                inf_df["month"] = 1
                inf_df = inf_df[["date", "year", "month", "inflation"]].sort_values("date").reset_index(drop=True)
                historical["inflation"] = inf_df
                logger.info(f"Historical inflation loaded: {len(inf_df)} observations "
                            f"({int(inf_df['year'].min())} - {int(inf_df['year'].max())})")
        except Exception as e:
            logger.error(f"Failed to load historical inflation: {e}")
            historical["inflation"] = pd.DataFrame()
    else:
        logger.error(f"Historical inflation file not found at: {HISTORICAL_INF_PATH}")
        logger.error("Please copy kenya_inflation_data.csv into data/historical/")
        historical["inflation"] = pd.DataFrame()

    return historical


def merge_with_historical(live_cleaned: dict) -> dict:
    """
    Merge live API data with historical baseline.
    Live data takes priority where dates overlap.
    Falls back gracefully to historical-only if live data is unavailable.

    INPUT:  live_cleaned — dict from cleaner.clean_all()
    OUTPUT: dict with merged DataFrames and a combined merged DataFrame
    """
    logger.info("Merging live data with historical baseline...")

    historical = load_historical_data()
    merged     = {}

    for series in ["inflation", "interest_rate"]:
        hist_df = historical.get(series, pd.DataFrame())
        live_df = live_cleaned.get(series, pd.DataFrame())

        # ── Case 1: Both empty ────────────────────────────────────────────────
        if hist_df.empty and live_df.empty:
            logger.error(f"Both historical and live {series} are empty. Cannot proceed.")
            merged[series] = pd.DataFrame()
            continue

        # ── Case 2: No live data — use historical only ────────────────────────
        if live_df.empty:
            logger.warning(f"No live {series} data available. Using historical data only.")
            merged[series] = hist_df.copy()
            continue

        # ── Case 3: No historical data — use live only ────────────────────────
        if hist_df.empty:
            logger.warning(f"No historical {series} data. Using live data only.")
            merged[series] = live_df.copy()
            continue

        # ── Case 4: Both available — merge, live takes priority ───────────────
        hist_df["date"] = pd.to_datetime(hist_df["date"])
        live_df["date"] = pd.to_datetime(live_df["date"])

        # Stack them — live data last so it wins on drop_duplicates keep='last'
        combined = pd.concat([hist_df, live_df], ignore_index=True)
        combined = combined.sort_values("date")
        combined = combined.drop_duplicates(subset=["date"], keep="last")
        combined = combined.sort_values("date").reset_index(drop=True)

        # Ensure consistent derived columns
        combined["year"]  = combined["date"].dt.year
        combined["month"] = combined["date"].dt.month

        merged[series] = combined
        logger.info(f"{series}: Merged — {len(combined)} observations "
                    f"({int(combined['year'].min())} - {int(combined['year'].max())})")

    # ── Build combined annual DataFrame for models ────────────────────────────
    merged["combined"] = _build_combined_annual(merged)

    # Pass through metadata
    merged["latest"]     = live_cleaned.get("latest", {})
    merged["fetch_time"] = live_cleaned.get("fetch_time")
    merged["success"]    = live_cleaned.get("success", False)
    merged["live_available"] = not (
        live_cleaned.get("inflation", pd.DataFrame()).empty and
        live_cleaned.get("interest_rate", pd.DataFrame()).empty
    )

    return merged


def _build_combined_annual(merged: dict) -> pd.DataFrame:
    """
    Build a single annual DataFrame with both interest_rate and inflation.
    This is what the structural models (VECM, GARCH, etc.) consume.

    Handles both annual and monthly source data gracefully.

    INPUT:  merged — dict with 'inflation' and 'interest_rate' DataFrames
    OUTPUT: Annual DataFrame with columns: year, interest_rate, inflation, real_rate
    """
    ir_df  = merged.get("interest_rate", pd.DataFrame())
    inf_df = merged.get("inflation",     pd.DataFrame())

    if ir_df.empty or inf_df.empty:
        logger.warning("Cannot build combined annual DataFrame — one or both series empty.")
        return pd.DataFrame()

    def to_annual(df, col):
        """Aggregate to annual average — works for both monthly and annual input."""
        if col not in df.columns:
            logger.error(f"Column '{col}' not found in DataFrame. Columns: {df.columns.tolist()}")
            return pd.DataFrame()
        if "year" not in df.columns:
            df = df.copy()
            df["year"] = pd.to_datetime(df["date"]).dt.year
        annual = df.groupby("year")[col].mean().reset_index()
        annual[col] = annual[col].round(4)
        return annual

    ir_annual  = to_annual(ir_df,  "interest_rate")
    inf_annual = to_annual(inf_df, "inflation")

    if ir_annual.empty or inf_annual.empty:
        return pd.DataFrame()

    combined = pd.merge(ir_annual, inf_annual, on="year", how="inner")
    combined = combined.sort_values("year").reset_index(drop=True)
    combined["real_rate"]    = (combined["interest_rate"] - combined["inflation"]).round(4)
    combined["above_target"] = combined["inflation"] > 7.5

    logger.info(f"Combined annual DataFrame ready: {len(combined)} years "
                f"({int(combined['year'].min())} - {int(combined['year'].max())})")

    return combined