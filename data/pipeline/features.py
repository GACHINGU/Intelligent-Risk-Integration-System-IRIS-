# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Feature Engineering
#
# Takes the merged, clean data and computes all the derived features
# that the models and dashboard need.
#
# Features computed here:
#   - Year-on-year changes (first differences)
#   - Rolling statistics (mean, std dev over 5 and 10 year windows)
#   - Real interest rate (nominal rate minus inflation)
#   - Inflation gap (inflation minus CBK target midpoint)
#   - Decade labels (for regime visualisation)
#   - Lag features (for Granger causality and cross-correlation)
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from config.settings import CBK_INFLATION_TARGET_MID, CBK_INFLATION_TARGET_UPPER
from utils.logger import get_logger

logger = get_logger(__name__)


def build_features(combined: pd.DataFrame) -> pd.DataFrame:
    """
    Add all derived features to the combined annual DataFrame.

    INPUT:  combined — annual DataFrame with year, interest_rate, inflation
    OUTPUT: enriched DataFrame with many additional columns
    """
    if combined is None or combined.empty:
        logger.warning("Cannot build features: combined DataFrame is empty.")
        return pd.DataFrame()

    df = combined.copy().sort_values("year").reset_index(drop=True)

    logger.info(f"Building features for {len(df)} annual observations...")

    # ── 1. Real interest rate ─────────────────────────────────────────────────
    # The REAL rate = what you actually earn after inflation eats into your return
    # Positive = savers are protected. Negative = money is losing value.
    df["real_rate"] = df["interest_rate"] - df["inflation"]

    # ── 2. Inflation gap from CBK target ──────────────────────────────────────
    # How far is inflation from the CBK's 5% midpoint target?
    df["inflation_gap"]       = df["inflation"] - CBK_INFLATION_TARGET_MID
    df["above_target"]        = df["inflation"] > CBK_INFLATION_TARGET_UPPER
    df["pct_above_target"]    = ((df["inflation"] - CBK_INFLATION_TARGET_UPPER)
                                  .clip(lower=0))

    # ── 3. Year-on-year changes (first differences) ───────────────────────────
    # Models need stationary data — first differences remove trends
    df["d_inflation"]     = df["inflation"].diff()
    df["d_interest_rate"] = df["interest_rate"].diff()
    df["d_real_rate"]     = df["real_rate"].diff()

    # ── 4. Rolling statistics (10-year window) ────────────────────────────────
    # Shows how average and volatility have changed over time
    df["roll10_inf_mean"]  = df["inflation"].rolling(10, min_periods=5).mean()
    df["roll10_inf_std"]   = df["inflation"].rolling(10, min_periods=5).std()
    df["roll10_ir_mean"]   = df["interest_rate"].rolling(10, min_periods=5).mean()
    df["roll10_ir_std"]    = df["interest_rate"].rolling(10, min_periods=5).std()
    df["roll10_rr_mean"]   = df["real_rate"].rolling(10, min_periods=5).mean()

    # ── 5. Rolling statistics (5-year window) — more responsive ───────────────
    df["roll5_inf_mean"]   = df["inflation"].rolling(5, min_periods=3).mean()
    df["roll5_inf_std"]    = df["inflation"].rolling(5, min_periods=3).std()
    df["roll5_ir_mean"]    = df["interest_rate"].rolling(5, min_periods=3).mean()

    # ── 6. Rolling correlation (10-year window) ───────────────────────────────
    df["roll10_corr"] = (df["interest_rate"]
                         .rolling(10, min_periods=7)
                         .corr(df["inflation"]))

    # ── 7. Lag features (for lead-lag and Granger analysis) ───────────────────
    for lag in [1, 2, 3]:
        df[f"inf_lag{lag}"]  = df["inflation"].shift(lag)
        df[f"ir_lag{lag}"]   = df["interest_rate"].shift(lag)

    # ── 8. Decade label (for regime visualisation) ────────────────────────────
    df["decade"]       = (df["year"] // 10) * 10
    df["decade_label"] = df["decade"].astype(str) + "s"

    # ── 9. Fisher gap ─────────────────────────────────────────────────────────
    # Fisher Effect says: nominal rate should equal real rate + expected inflation
    # Fisher gap = how far current nominal rate deviates from what Fisher predicts
    df["fisher_gap"] = df["interest_rate"] - df["inflation"]   # same as real_rate

    # ── 10. Stress indicator (simple composite before the full IRIS score) ────
    # Quick heuristic: are we stressed?
    # Gives 1 point for each stress condition, max 4 points
    df["stress_raw"] = (
        (df["inflation"]     > 10).astype(int) +   # Inflation above 10%
        (df["real_rate"]     < 0 ).astype(int) +   # Negative real rate
        (df["roll10_inf_std"]> 5 ).astype(int) +   # High inflation volatility
        (df["d_inflation"]   > 3 ).astype(int)     # Inflation accelerating fast
    )

    logger.info(f"Features built. DataFrame now has {len(df.columns)} columns.")

    return df