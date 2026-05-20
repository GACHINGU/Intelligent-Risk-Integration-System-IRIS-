# ─────────────────────────────────────────────────────────────────────────────
# IRIS — VECM (Vector Error Correction Model)
#
# WHAT IS A VECM? (Plain English)
# A VECM is the core structural model when two series are cointegrated.
# It does two things simultaneously:
#
#   1. SHORT-RUN DYNAMICS: How does last year's interest rate affect
#      this year's inflation? How does last year's inflation affect
#      this year's interest rate? (The VAR part)
#
#   2. LONG-RUN CORRECTION: If interest rates and inflation drift too far
#      apart from their equilibrium relationship, the VECM models the
#      speed at which they correct back. (The error correction part)
#
# KEY OUTPUTS:
#   - Alpha (adjustment speeds): how fast each variable corrects
#   - Beta (cointegrating vector): the long-run equation
#   - Short-run coefficients: the immediate dynamic responses
#
# FOR IRIS:
#   Alpha tells us whether the CBK is PROACTIVE (rates lead) or
#   REACTIVE (rates follow inflation). This is a key policy signal.
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from statsmodels.tsa.vector_ar.vecm import VECM
from utils.logger import get_logger

logger = get_logger(__name__)


def run_vecm(df: pd.DataFrame,
             coint_rank: int = 1,
             k_ar_diff: int = 1,
             deterministic: str = "ci") -> dict:
    """
    Fit a VECM on interest_rate and inflation.

    INPUT:
        df            — annual DataFrame with interest_rate and inflation
        coint_rank    — cointegration rank from Johansen test (default 1)
        k_ar_diff     — number of lagged differences (default 1)
        deterministic — 'ci' = constant inside cointegrating equation

    OUTPUT: dict with fitted model, key parameters, and interpretations
    """
    required = ["interest_rate", "inflation"]
    data     = df[required].dropna()

    if len(data) < 20:
        logger.error("VECM: insufficient data.")
        return {"error": "Insufficient data", "fitted": None}

    # Ensure at least 1 lag
    k_ar_diff = max(1, k_ar_diff)

    try:
        # ── Fit the VECM ──────────────────────────────────────────────────────
        model     = VECM(data, coint_rank=coint_rank,
                         k_ar_diff=k_ar_diff, deterministic=deterministic)
        fitted    = model.fit()

        # ── Extract alpha (adjustment speeds) ─────────────────────────────────
        # alpha[0] = how fast interest_rate adjusts to restore equilibrium
        # alpha[1] = how fast inflation adjusts to restore equilibrium
        # More negative alpha = faster adjustment
        alpha_ir  = round(float(fitted.alpha[0, 0]), 4)
        alpha_inf = round(float(fitted.alpha[1, 0]), 4)

        # ── Extract beta (long-run cointegrating vector) ───────────────────────
        # By convention: interest_rate = constant + beta * inflation
        # beta[1, 0] is the coefficient on inflation in the long-run equation
        beta_inf  = round(float(fitted.beta[1, 0]), 4)

        # ── Determine who adjusts more ────────────────────────────────────────
        # The variable with the LARGER absolute alpha adjusts more
        # = that variable is more "reactive" / "follower"
        # The other variable is the "driver"
        ir_adjusts_more  = abs(alpha_ir) > abs(alpha_inf)
        policy_character = "REACTIVE" if ir_adjusts_more else "PROACTIVE"

        # ── Long-run relationship interpretation ───────────────────────────────
        if beta_inf > 0:
            lr_direction = "POSITIVE"
            lr_plain = (
                f"In the long run, a 1% rise in inflation is associated with "
                f"a {beta_inf:.2f}% rise in interest rates. "
                f"This is CONSISTENT with the Fisher Effect — rates rise with inflation."
            )
        else:
            lr_direction = "NEGATIVE"
            lr_plain = (
                f"In the long run, higher inflation is associated with LOWER interest rates. "
                f"This is INCONSISTENT with the Fisher Effect — suggesting fiscal dominance "
                f"or supply-driven inflation that rates cannot fully address."
            )

        # ── Policy character interpretation ───────────────────────────────────
        if ir_adjusts_more:
            policy_plain = (
                f"Interest rates adjust MORE to restore equilibrium (alpha = {alpha_ir:.4f}). "
                f"This means INFLATION tends to drift first, and the CBK's interest rate "
                f"FOLLOWS it back to equilibrium. "
                f"This is characteristic of REACTIVE monetary policy — "
                f"the CBK responds after inflation has already moved."
            )
        else:
            policy_plain = (
                f"Inflation adjusts MORE to restore equilibrium (alpha = {alpha_inf:.4f}). "
                f"This means INTEREST RATES tend to move first, and inflation "
                f"corrects back toward them. "
                f"This is characteristic of PROACTIVE monetary policy — "
                f"the CBK moves ahead of inflation."
            )

        # ── Half-life of deviation ────────────────────────────────────────────
        # How many years before half of a deviation from equilibrium is corrected?
        # Formula: half_life = log(0.5) / log(1 - |alpha|)
        try:
            dominant_alpha = max(abs(alpha_ir), abs(alpha_inf))
            if 0 < dominant_alpha < 1:
                half_life = round(np.log(0.5) / np.log(1 - dominant_alpha), 1)
            else:
                half_life = None
        except Exception:
            half_life = None

        result = {
            "fitted":           fitted,
            "summary":          str(fitted.summary()),
            "coint_rank":       coint_rank,
            "k_ar_diff":        k_ar_diff,
            "n_obs":            len(data),

            # Long-run relationship
            "beta_inflation":   beta_inf,
            "lr_direction":     lr_direction,
            "lr_plain":         lr_plain,

            # Adjustment speeds
            "alpha_ir":         alpha_ir,
            "alpha_inf":        alpha_inf,
            "ir_adjusts_more":  ir_adjusts_more,
            "policy_character": policy_character,
            "policy_plain":     policy_plain,

            # Half-life
            "half_life_years":  half_life,
            "half_life_plain": (
                f"After a shock, approximately half the deviation from equilibrium "
                f"is corrected within {half_life} year(s)."
                if half_life else "Half-life could not be computed."
            ),
        }

        logger.info(f"VECM fitted. Alpha IR={alpha_ir:.4f}, Inf={alpha_inf:.4f}. "
                    f"Beta={beta_inf:.4f}. Policy: {policy_character}. "
                    f"Half-life: {half_life} yrs.")

        return result

    except Exception as e:
        logger.error(f"VECM fitting failed: {e}")
        return {"error": str(e), "fitted": None}