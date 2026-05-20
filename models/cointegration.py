# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Cointegration Testing (Johansen Test)
#
# WHAT IS COINTEGRATION? (Plain English)
# Imagine two dogs on a shared leash being walked together.
# Each dog wanders freely — but they can never go too far apart.
# In the long run, they stay connected even if they move independently
# in the short run.
#
# If interest rates and inflation are COINTEGRATED:
#   → They share a long-run equilibrium relationship
#   → The CBK's rate decisions genuinely anchor inflation over time
#   → We use VECM (which models the correction back to equilibrium)
#
# If NOT cointegrated:
#   → The series drift apart permanently
#   → Monetary policy only has temporary effects
#   → We use VAR in differences instead
#
# The Johansen test is the gold standard for cointegration testing.
# It tells us HOW MANY cointegrating relationships exist (the rank r).
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from statsmodels.tsa.vector_ar.vecm import select_coint_rank, select_order
from statsmodels.tsa.stattools import coint
from utils.logger import get_logger

logger = get_logger(__name__)


def run_johansen(df: pd.DataFrame,
                 det_order: int = 0,
                 signif: float = 0.05) -> dict:
    """
    Run the Johansen cointegration test on interest_rate and inflation.

    INPUT:
        df        — annual DataFrame with interest_rate and inflation columns
        det_order — 0 = constant inside cointegrating equation (standard)
        signif    — significance level (default 5%)

    OUTPUT: dict with test results, rank, and plain-English interpretation
    """
    required = ["interest_rate", "inflation"]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        logger.error(f"Johansen test: missing columns {missing}")
        return {"error": f"Missing columns: {missing}", "rank": 0, "cointegrated": False}

    data = df[required].dropna()

    if len(data) < 20:
        logger.error(f"Johansen test: insufficient data ({len(data)} observations).")
        return {"error": "Insufficient data", "rank": 0, "cointegrated": False}

    try:
        # ── Step 1: Select optimal lag order ─────────────────────────────────
        # We look at up to 6 lags and let AIC choose the best
        lag_result  = select_order(data, maxlags=6, deterministic="ci")
        optimal_lag = max(1, lag_result.aic)
        logger.info(f"Johansen: optimal lag order by AIC = {optimal_lag}")

        # ── Step 2: Run Johansen trace test ───────────────────────────────────
        # method='trace' is the most widely used approach
        # Tests H0: rank = 0 (no cointegration) vs H1: rank >= 1
        johansen = select_coint_rank(
            data,
            det_order=det_order,
            k_ar_diff=optimal_lag,
            method="trace",
            signif=signif,
        )

        rank        = johansen.rank
        cointegrated = rank >= 1

        # ── Step 3: Also run Engle-Granger as a cross-check ──────────────────
        eg_stat, eg_p, _ = coint(data["interest_rate"], data["inflation"])
        eg_cointegrated  = eg_p < signif

        # ── Plain English interpretation ──────────────────────────────────────
        if cointegrated:
            interpretation = (
                f"COINTEGRATION CONFIRMED (rank = {rank}). "
                f"Interest rates and inflation share a long-run equilibrium relationship. "
                f"When they drift apart, forces pull them back together. "
                f"This validates Kenya's inflation-targeting framework. "
                f"VECM is the appropriate model."
            )
        else:
            interpretation = (
                f"NO COINTEGRATION DETECTED (rank = {rank}). "
                f"Interest rates and inflation do not share a stable long-run relationship. "
                f"Monetary policy effects on inflation may be temporary only. "
                f"VAR in first differences is the appropriate model."
            )

        result = {
            "rank":              rank,
            "cointegrated":      cointegrated,
            "optimal_lag":       optimal_lag,
            "det_order":         det_order,
            "significance":      signif,
            "n_obs":             len(data),

            # Johansen trace results
            "johansen_summary":  str(johansen.summary()),

            # Engle-Granger cross-check
            "eg_statistic":      round(eg_stat, 4),
            "eg_p_value":        round(eg_p, 4),
            "eg_cointegrated":   eg_cointegrated,

            # Agreement between the two tests
            "tests_agree":       cointegrated == eg_cointegrated,

            # For the risk engine and dashboard
            "interpretation":    interpretation,
            "model_choice":      "VECM" if cointegrated else "VAR",

            # Plain English for the memorandum
            "plain_english": (
                "Kenya's interest rates and inflation ARE connected in the long run. "
                "The CBK's rate decisions have a genuine long-run anchor on inflation. "
                "Short-term deviations correct over time."
                if cointegrated else
                "Kenya's interest rates and inflation are NOT consistently connected long-term. "
                "Rate changes produce temporary effects on inflation but no lasting equilibrium."
            ),
        }

        logger.info(f"Johansen test complete. Rank = {rank}. "
                    f"Cointegrated: {cointegrated}. Model: {result['model_choice']}")

        return result

    except Exception as e:
        logger.error(f"Johansen cointegration test failed: {e}")
        return {
            "error":        str(e),
            "rank":         0,
            "cointegrated": False,
            "model_choice": "VAR",
        }