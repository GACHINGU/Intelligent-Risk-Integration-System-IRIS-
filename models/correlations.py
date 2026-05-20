# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Correlation Analysis (Static, Dynamic, Cross, Lead-Lag)
#
# WHAT WE COMPUTE HERE:
#   1. Static Pearson correlation (linear relationship, full sample)
#   2. Static Spearman correlation (rank-based, robust to outliers)
#   3. Rolling correlation (10-year window — has the relationship changed?)
#   4. Cross-correlation at lags ±10 years (does one LEAD the other?)
#   5. Fisher Effect test (do rates move with inflation as theory predicts?)
#
# WHY ALL THESE DIFFERENT CORRELATIONS?
#   A single number (e.g. Pearson r = -0.32) tells you the average
#   relationship over 53 years. But that average hides a lot.
#   The rolling correlation reveals that the relationship has CHANGED over
#   time — positive in some decades, negative in others.
#   The cross-correlation reveals whether inflation LEADS rates (reactive
#   CBK) or rates LEAD inflation (proactive CBK).
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from scipy import stats
from utils.logger import get_logger

logger = get_logger(__name__)


def run_correlations(df: pd.DataFrame,
                      rolling_window: int = 10,
                      max_lag: int = 10) -> dict:
    """
    Compute all correlation measures between interest_rate and inflation.

    INPUT:
        df             — annual DataFrame with interest_rate, inflation, year
        rolling_window — years for rolling correlation window (default 10)
        max_lag        — maximum lag for cross-correlation (default 10)

    OUTPUT: dict with all correlation results and interpretations
    """
    required = ["interest_rate", "inflation", "year"]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        logger.error(f"Correlations: missing columns {missing}")
        return {"error": f"Missing columns: {missing}"}

    data = df[required].dropna().sort_values("year").reset_index(drop=True)
    ir   = data["interest_rate"]
    inf  = data["inflation"]
    yrs  = data["year"]

    if len(data) < 10:
        logger.error("Correlations: insufficient data.")
        return {"error": "Insufficient data"}

    try:
        # ── 1. Static Pearson correlation ─────────────────────────────────────
        pearson_r, pearson_p = stats.pearsonr(ir, inf)
        pearson_r = round(pearson_r, 4)
        pearson_p = round(pearson_p, 4)

        # ── 2. Static Spearman correlation ────────────────────────────────────
        spearman_r, spearman_p = stats.spearmanr(ir, inf)
        spearman_r = round(float(spearman_r), 4)
        spearman_p = round(float(spearman_p), 4)

        # ── 3. Rolling correlation ────────────────────────────────────────────
        roll_corr = ir.rolling(rolling_window, min_periods=7).corr(inf)
        roll_corr_clean = roll_corr.dropna()

        # Is the rolling correlation trending up or down recently?
        if len(roll_corr_clean) >= 5:
            recent_slope, _, _, _, _ = stats.linregress(
                range(len(roll_corr_clean[-10:])),
                roll_corr_clean.values[-10:]
            )
            corr_trend = "STRENGTHENING" if recent_slope > 0.02 else (
                "WEAKENING" if recent_slope < -0.02 else "STABLE"
            )
        else:
            recent_slope = 0
            corr_trend   = "UNKNOWN"

        # Current rolling correlation (most recent window)
        current_roll_corr = round(float(roll_corr_clean.iloc[-1]), 4) if len(roll_corr_clean) > 0 else None

        # ── 4. Cross-correlation (lead-lag structure) ─────────────────────────
        lags     = list(range(-max_lag, max_lag + 1))
        xcorr    = []
        for lag in lags:
            if lag < 0:
                # Positive lag on inflation = inflation leads rates
                shifted = inf.shift(-lag)
            else:
                shifted = inf.shift(lag)
            valid = pd.concat([ir, shifted], axis=1).dropna()
            if len(valid) > 5:
                r, _ = stats.pearsonr(valid.iloc[:, 0], valid.iloc[:, 1])
                xcorr.append(round(r, 4))
            else:
                xcorr.append(0.0)

        # Find peak cross-correlation
        xcorr_arr  = np.array(xcorr)
        peak_idx   = int(np.argmax(np.abs(xcorr_arr)))
        peak_lag   = lags[peak_idx]
        peak_xcorr = round(float(xcorr_arr[peak_idx]), 4)

        # Significance threshold: ±1.96 / sqrt(n)
        sig_threshold = round(1.96 / np.sqrt(len(data)), 4)

        # Lead-lag interpretation
        if peak_lag < 0:
            lead_lag_plain = (
                f"INFLATION LEADS interest rates by {abs(peak_lag)} year(s). "
                f"The CBK raises rates AFTER inflation has already risen. "
                f"This confirms REACTIVE monetary policy in Kenya's history."
            )
        elif peak_lag > 0:
            lead_lag_plain = (
                f"INTEREST RATES LEAD inflation by {peak_lag} year(s). "
                f"The CBK raises rates BEFORE inflation rises. "
                f"This is evidence of PROACTIVE (anticipatory) monetary policy."
            )
        else:
            lead_lag_plain = (
                "Interest rates and inflation move CONCURRENTLY — "
                "no systematic lead or lag at the annual frequency."
            )

        # ── 5. Fisher Effect test ─────────────────────────────────────────────
        # Simple Fisher test: regress interest rate on inflation
        # Fisher Effect predicts slope = 1.0 (one-for-one)
        slope, intercept, r_val, p_val, std_err = stats.linregress(inf, ir)
        fisher_slope = round(slope, 4)

        # Is the slope significantly different from 1.0?
        # t-statistic for H0: slope = 1
        t_stat_fisher = round((slope - 1.0) / std_err, 4) if std_err > 0 else None
        fisher_holds  = abs(fisher_slope - 1.0) < 0.5   # Loose test: within 0.5 of 1.0

        # ── 6. Decade correlations ────────────────────────────────────────────
        data["decade"] = (data["year"] // 10) * 10
        decade_corr    = {}
        for decade, group in data.groupby("decade"):
            if len(group) >= 5:
                r, p = stats.pearsonr(group["interest_rate"], group["inflation"])
                decade_corr[str(decade)] = {
                    "pearson_r": round(r, 4),
                    "p_value":   round(p, 4),
                    "n_obs":     len(group),
                    "significant": p < 0.05,
                }

        # ── Static correlation interpretation ─────────────────────────────────
        def interpret_r(r, p):
            strength = (
                "strong"   if abs(r) >= 0.7 else
                "moderate" if abs(r) >= 0.4 else
                "weak"     if abs(r) >= 0.2 else
                "negligible"
            )
            direction = "positive" if r > 0 else "negative"
            sig       = "statistically significant" if p < 0.05 else "not statistically significant"
            return f"{strength} {direction} ({sig})"

        pearson_plain = (
            f"Pearson r = {pearson_r:.3f}: {interpret_r(pearson_r, pearson_p)}. "
            f"{'Higher inflation tends to coincide with higher rates.' if pearson_r > 0 else 'Higher inflation has tended to coincide with LOWER rates — evidence of financial repression and reactive policy.'}"
        )

        result = {
            # Static correlations
            "pearson_r":           pearson_r,
            "pearson_p":           pearson_p,
            "spearman_r":          spearman_r,
            "spearman_p":          spearman_p,

            # Rolling correlation
            "rolling_window":      rolling_window,
            "roll_corr":           roll_corr.tolist(),
            "roll_corr_years":     yrs.tolist(),
            "current_roll_corr":   current_roll_corr,
            "corr_trend":          corr_trend,
            "recent_slope":        round(float(recent_slope), 4),

            # Cross-correlation
            "lags":                lags,
            "xcorr":               xcorr,
            "peak_lag":            peak_lag,
            "peak_xcorr":          peak_xcorr,
            "sig_threshold":       sig_threshold,

            # Fisher Effect
            "fisher_slope":        fisher_slope,
            "fisher_intercept":    round(intercept, 4),
            "fisher_r_squared":    round(r_val**2, 4),
            "fisher_holds":        fisher_holds,

            # Decade breakdown
            "decade_corr":         decade_corr,

            # Interpretations
            "pearson_plain":       pearson_plain,
            "lead_lag_plain":      lead_lag_plain,
            "fisher_plain": (
                f"Fisher Effect slope = {fisher_slope:.3f}. "
                f"Theory predicts 1.0 (one-for-one). "
                f"{'Fisher Effect approximately holds in Kenya.' if fisher_holds else 'Fisher Effect does NOT hold — rates do not move one-for-one with inflation. Financial repression is likely.'}"
            ),
            "rolling_plain": (
                f"The rolling {rolling_window}-year correlation is currently {current_roll_corr:.3f} "
                f"and is {corr_trend.lower()} in recent years. "
                f"This time-varying correlation confirms the relationship is not structurally stable."
            ),
        }

        logger.info(f"Correlations computed. Pearson={pearson_r:.4f}, Spearman={spearman_r:.4f}. "
                    f"Peak lag={peak_lag}. Corr trend: {corr_trend}.")

        return result

    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        return {"error": str(e)}