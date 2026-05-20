# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Markov Regime-Switching Model
#
# WHAT IS REGIME SWITCHING? (Plain English)
# The economy does not always behave the same way.
# Sometimes Kenya is in a CALM period — low inflation, predictable prices.
# Sometimes Kenya is in a STRESSED period — high inflation, prices spiking.
#
# The Markov Regime-Switching model:
#   1. Automatically identifies these two "modes" (regimes)
#   2. Estimates the PROBABILITY of being in each regime at each point in time
#   3. Estimates how likely a SWITCH between regimes is
#
# KEY OUTPUT FOR IRIS:
#   - Current probability of being in the high-inflation regime
#   - Probability of switching to the high-inflation regime next year
#   - Historical timeline of regime periods
#   - Early warning signal: P(high-inflation) > 50% = danger zone
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from statsmodels.tsa.regime_switching.markov_autoregression import MarkovAutoregression
from utils.logger import get_logger

logger = get_logger(__name__)


def _extract_regime_means(fitted, k_regimes: int, fallback_mean: float) -> list:
    """
    Safely extract the mean inflation level for each regime from fitted params.
    Handles different statsmodels parameter naming conventions.
    """
    means = []
    params = fitted.params

    for r in range(k_regimes):
        found = False
        # Try several naming conventions statsmodels uses
        for key in [f"const[{r}]", f"intercept[{r}]", f"mean[{r}]"]:
            if key in params.index:
                means.append(float(params[key]))
                found = True
                break

        if not found:
            # Fall back: scan params for anything that looks like a regime constant
            # Regime-specific params appear first in the param vector
            # For AR(1) with k regimes: first k params are regime means
            try:
                means.append(float(params.iloc[r]))
            except Exception:
                means.append(fallback_mean)

    return means


def run_regime_switching(df: pd.DataFrame,
                          k_regimes: int = 2,
                          order: int = 1) -> dict:
    """
    Fit a Markov Regime-Switching AR model on Kenya's inflation.

    INPUT:
        df        — annual DataFrame with inflation column and year column
        k_regimes — number of regimes (default 2: calm and stressed)
        order     — AR order inside each regime (default 1)

    OUTPUT: dict with fitted model, regime probabilities, and interpretations
    """
    if "inflation" not in df.columns:
        logger.error("Regime switching: 'inflation' column not found.")
        return {"error": "No inflation column"}

    # Work only with clean inflation values
    clean_df = df[["year", "inflation"]].dropna().sort_values("year").reset_index(drop=True)
    inf_data  = clean_df["inflation"].values.astype(float)
    years     = clean_df["year"].values

    if len(inf_data) < 20:
        logger.error(f"Regime switching: insufficient data ({len(inf_data)} obs).")
        return {"error": "Insufficient data"}

    try:
        # ── Fit Markov AR(1) with switching variance ───────────────────────────
        # switching_variance=True: each regime has its own volatility level
        model  = MarkovAutoregression(
            inf_data,
            k_regimes=k_regimes,
            order=order,
            switching_variance=True,
        )
        fitted = model.fit(disp=False, maxiter=200)

        # ── Get smoothed regime probabilities ──────────────────────────────────
        # Shape: (T, k_regimes)
        # Handle both numpy array and DataFrame outputs from statsmodels
        raw_probs    = fitted.smoothed_marginal_probabilities
        smooth_probs = np.array(raw_probs)   # always numpy from here on
        n_smooth     = len(smooth_probs)

        # Align years to smoothed probs length (AR(1) loses first observation)
        plot_years = years[:n_smooth]

        # ── Identify which regime is HIGH-INFLATION ────────────────────────────
        regime_means = _extract_regime_means(fitted, k_regimes, float(np.mean(inf_data)))
        logger.info(f"Regime means extracted: {[round(m,2) for m in regime_means]}")

        high_regime = int(np.argmax(regime_means))
        low_regime  = 1 - high_regime   # Works cleanly for k=2

        # ── Current regime probability ─────────────────────────────────────────
        # Use plain numpy indexing — works regardless of statsmodels version
        current_p_high = round(float(smooth_probs[-1, high_regime]), 4)
        current_p_low  = round(float(smooth_probs[-1, low_regime]),  4)
        current_regime = "HIGH_INFLATION" if current_p_high > 0.5 else "LOW_INFLATION"

        # ── Transition probabilities ───────────────────────────────────────────
        trans = fitted.transition_matrix
        # trans shape: (k_regimes, k_regimes)
        # trans[to_regime, from_regime]
        p_stay_low    = round(float(trans[low_regime,  low_regime]),  4)
        p_low_to_high = round(float(trans[high_regime, low_regime]),  4)
        p_stay_high   = round(float(trans[high_regime, high_regime]), 4)
        p_high_to_low = round(float(trans[low_regime,  high_regime]), 4)

        # Expected duration in each regime = 1 / (1 - P_stay)
        duration_low  = round(1 / max(1 - p_stay_low,  0.001), 1)
        duration_high = round(1 / max(1 - p_stay_high, 0.001), 1)

        # ── Regime timeline ────────────────────────────────────────────────────
        # For each year: which regime was dominant?
        prob_high_series = [
            round(float(smooth_probs[t, high_regime]), 4)
            for t in range(n_smooth)
        ]
        prob_low_series = [
            round(float(smooth_probs[t, low_regime]), 4)
            for t in range(n_smooth)
        ]
        regime_labels = [
            "HIGH" if p > 0.5 else "LOW"
            for p in prob_high_series
        ]

        high_years = [int(plot_years[t]) for t in range(n_smooth) if regime_labels[t] == "HIGH"]
        low_years  = [int(plot_years[t]) for t in range(n_smooth) if regime_labels[t] == "LOW"]

        # ── Plain English interpretations ──────────────────────────────────────
        if current_p_high > 0.8:
            regime_signal = "CRITICAL"
            regime_plain  = (
                f"Kenya is currently in the HIGH-INFLATION regime with "
                f"{current_p_high*100:.0f}% confidence. "
                f"This is comparable to Kenya's historical crisis periods (1993, 2008). "
                f"Immediate and decisive policy response is required."
            )
        elif current_p_high > 0.5:
            regime_signal = "DANGER"
            regime_plain  = (
                f"Kenya is in the HIGH-INFLATION regime "
                f"(probability: {current_p_high*100:.0f}%). "
                f"The system has crossed the 50% warning threshold. "
                f"Proactive policy tightening is advised."
            )
        elif current_p_high > 0.3:
            regime_signal = "MODERATE"
            regime_plain  = (
                f"Kenya shows elevated risk of transitioning to the "
                f"HIGH-INFLATION regime (probability: {current_p_high*100:.0f}%). "
                f"Increased monitoring is warranted."
            )
        else:
            regime_signal = "STABLE"
            regime_plain  = (
                f"Kenya is in the LOW-INFLATION regime "
                f"(probability: {current_p_low*100:.0f}%). "
                f"Conditions are relatively stable from a regime perspective."
            )

        persistence_plain = (
            f"Once in the HIGH-INFLATION regime, there is a {p_stay_high*100:.0f}% "
            f"chance of STAYING there next year "
            f"(expected duration: {duration_high:.1f} years). "
            f"Once in the LOW-INFLATION regime, there is a {p_stay_low*100:.0f}% "
            f"chance of STAYING there "
            f"(expected duration: {duration_low:.1f} years)."
        )

        result = {
            "fitted":               fitted,
            "k_regimes":            k_regimes,
            "n_obs":                n_smooth,

            # Probability series (for plotting)
            "prob_high":            prob_high_series,
            "prob_low":             prob_low_series,
            "years":                plot_years.tolist(),

            # Current reading
            "current_p_high":       current_p_high,
            "current_p_low":        current_p_low,
            "current_regime":       current_regime,
            "regime_signal":        regime_signal,

            # Transition matrix
            "p_stay_low":           p_stay_low,
            "p_low_to_high":        p_low_to_high,
            "p_stay_high":          p_stay_high,
            "p_high_to_low":        p_high_to_low,

            # Expected durations
            "duration_low_yrs":     duration_low,
            "duration_high_yrs":    duration_high,

            # Timeline
            "regime_labels":        regime_labels,
            "high_inflation_years": high_years,
            "low_inflation_years":  low_years,

            # Regime characteristics
            "mean_low_regime":      round(min(regime_means), 4),
            "mean_high_regime":     round(max(regime_means), 4),

            # Interpretations
            "regime_plain":         regime_plain,
            "persistence_plain":    persistence_plain,
        }

        logger.info(
            f"Regime switching fitted. "
            f"Regime means: low={result['mean_low_regime']:.2f}%, "
            f"high={result['mean_high_regime']:.2f}%. "
            f"Current P(high)={current_p_high:.4f}. "
            f"Signal: {regime_signal}. "
            f"High-inflation years: {len(high_years)}. "
            f"Low-inflation years: {len(low_years)}."
        )

        return result

    except Exception as e:
        logger.error(f"Regime switching model failed: {e}")
        return {"error": str(e)}