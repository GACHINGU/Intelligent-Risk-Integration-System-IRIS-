# ─────────────────────────────────────────────────────────────────────────────
# IRIS — GARCH(1,1) Volatility Model
#
# WHAT IS GARCH? (Plain English)
# GARCH models how UNCERTAIN (volatile) inflation is at any given time.
# Standard models assume uncertainty is constant — the same every year.
# GARCH allows uncertainty to CHANGE over time.
#
# Think of it like this:
#   Calm year → low uncertainty → you can budget confidently
#   Crisis year → high uncertainty → prices could go anywhere
#
# GARCH captures the fact that volatility CLUSTERS:
#   Bad times (high volatility) tend to follow bad times.
#   Calm times tend to follow calm times.
#
# KEY OUTPUT FOR IRIS:
#   - Current conditional volatility: how uncertain is inflation RIGHT NOW?
#   - Persistence: if volatility is high today, how long will it stay high?
#   - Historical volatility timeline: when were the most dangerous periods?
#
# WHY STUDENT-T DISTRIBUTION?
#   Kenya's inflation is fat-tailed (excess kurtosis +5.89).
#   A normal distribution underestimates extreme events.
#   Student-t handles fat tails correctly.
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from arch import arch_model
from utils.logger import get_logger

logger = get_logger(__name__)


def run_garch(df: pd.DataFrame,
              p: int = 1,
              q: int = 1,
              dist: str = "t") -> dict:
    """
    Fit a GARCH(1,1) model on Kenya's inflation series.

    INPUT:
        df   — annual DataFrame with inflation column
        p    — GARCH lag order (default 1)
        q    — ARCH lag order (default 1)
        dist — error distribution: 't' for Student-t (recommended for Kenya)

    OUTPUT: dict with fitted model, volatility series, and interpretations
    """
    if "inflation" not in df.columns:
        logger.error("GARCH: 'inflation' column not found.")
        return {"error": "No inflation column"}

    inflation = df["inflation"].dropna().values.astype(float)
    years     = df.loc[df["inflation"].notna(), "year"].values

    if len(inflation) < 20:
        logger.error(f"GARCH: insufficient data ({len(inflation)} observations).")
        return {"error": "Insufficient data"}

    try:
        # ── Fit GARCH(1,1) ────────────────────────────────────────────────────
        garch = arch_model(
            inflation,
            vol="Garch",
            p=p, q=q,
            dist=dist,
            mean="Constant",   # Allow a constant mean inflation level
        )
        fitted = garch.fit(disp="off")   # disp="off" = quiet mode, no convergence output

        # ── Extract parameters ────────────────────────────────────────────────
        params = fitted.params

        # Mean inflation estimate
        mu = round(float(params.get("Const", params.iloc[0])), 4)

        # ARCH effect (alpha): how much last year's shock affects this year's volatility
        alpha_key = [k for k in params.index if "alpha" in k.lower()]
        alpha = round(float(params[alpha_key[0]]), 4) if alpha_key else None

        # GARCH effect (beta): how much last year's volatility carries forward
        beta_key = [k for k in params.index if "beta" in k.lower()]
        beta = round(float(params[beta_key[0]]), 4) if beta_key else None

        # Omega (baseline variance)
        omega_key = [k for k in params.index if "omega" in k.lower()]
        omega = round(float(params[omega_key[0]]), 4) if omega_key else None

        # ── Persistence ───────────────────────────────────────────────────────
        # Persistence = alpha + beta
        # Close to 1.0 = volatility is very slow to decay
        # Above 1.0 = explosive (non-stationary volatility — concerning)
        persistence = round((alpha or 0) + (beta or 0), 4)

        # ── Conditional volatility series ─────────────────────────────────────
        # This is the model's estimate of how uncertain inflation was each year
        cond_vol = fitted.conditional_volatility

        # ── Current volatility reading ────────────────────────────────────────
        current_vol   = round(float(cond_vol[-1]), 4)
        historical_avg = round(float(np.mean(cond_vol)), 4)

        # Relative to historical average
        vol_ratio = round(current_vol / historical_avg, 2) if historical_avg > 0 else None

        # ── Find peak volatility years ────────────────────────────────────────
        vol_series = pd.Series(cond_vol, index=years)
        top3_vol   = vol_series.nlargest(3)

        # ── Long-run variance ─────────────────────────────────────────────────
        # If persistence < 1: long-run variance = omega / (1 - alpha - beta)
        if persistence < 1 and omega and (1 - persistence) > 0:
            lr_variance = round(omega / (1 - persistence), 4)
            lr_std      = round(float(np.sqrt(lr_variance)), 4)
        else:
            lr_variance = None
            lr_std      = None

        # ── Current risk level from GARCH ─────────────────────────────────────
        if vol_ratio is not None:
            if vol_ratio < 0.75:
                garch_risk = "LOW"
                garch_risk_plain = (
                    f"Current inflation volatility ({current_vol:.2f}) is BELOW the historical average. "
                    f"Prices are relatively predictable. Good conditions for household and business planning."
                )
            elif vol_ratio < 1.25:
                garch_risk = "MODERATE"
                garch_risk_plain = (
                    f"Current inflation volatility ({current_vol:.2f}) is NEAR the historical average. "
                    f"Moderate uncertainty — monitor for trends."
                )
            elif vol_ratio < 1.75:
                garch_risk = "ELEVATED"
                garch_risk_plain = (
                    f"Current inflation volatility ({current_vol:.2f}) is ABOVE the historical average "
                    f"by a factor of {vol_ratio:.1f}x. Uncertainty is elevated. "
                    f"The MPC should increase monitoring frequency."
                )
            else:
                garch_risk = "HIGH"
                garch_risk_plain = (
                    f"Current inflation volatility ({current_vol:.2f}) is significantly ABOVE "
                    f"the historical average ({vol_ratio:.1f}x). "
                    f"This level is comparable to Kenya's crisis periods. "
                    f"Decisive policy action is warranted."
                )
        else:
            garch_risk       = "UNKNOWN"
            garch_risk_plain = "Volatility risk level could not be determined."

        # ── Persistence interpretation ─────────────────────────────────────────
        if persistence > 0.95:
            persistence_plain = (
                f"Volatility persistence = {persistence:.4f} (very high). "
                f"Once Kenya enters a volatile inflation period, it tends to stay there for YEARS. "
                f"The MPC should act EARLY and DECISIVELY — do not wait for volatility to self-resolve."
            )
        elif persistence > 0.80:
            persistence_plain = (
                f"Volatility persistence = {persistence:.4f} (moderate-high). "
                f"Volatility clusters are present but will eventually dissipate with stable policy."
            )
        else:
            persistence_plain = (
                f"Volatility persistence = {persistence:.4f} (low-moderate). "
                f"Inflation shocks dissipate relatively quickly. "
                f"Monetary policy has a reasonable ability to stabilise expectations."
            )

        result = {
            "fitted":             fitted,
            "n_obs":              len(inflation),

            # Parameters
            "mu":                 mu,
            "alpha":              alpha,
            "beta":               beta,
            "omega":              omega,
            "persistence":        persistence,

            # Volatility series
            "cond_vol":           cond_vol.tolist(),
            "years":              years.tolist(),
            "current_vol":        current_vol,
            "historical_avg_vol": historical_avg,
            "vol_ratio":          vol_ratio,

            # Long-run
            "lr_variance":        lr_variance,
            "lr_std":             lr_std,

            # Peak years
            "peak_vol_years":     top3_vol.index.tolist(),
            "peak_vol_values":    top3_vol.values.tolist(),

            # Risk assessment
            "garch_risk":         garch_risk,
            "garch_risk_plain":   garch_risk_plain,
            "persistence_plain":  persistence_plain,
        }

        logger.info(f"GARCH fitted. Persistence={persistence:.4f}. "
                    f"Current vol={current_vol:.4f} vs avg={historical_avg:.4f} "
                    f"(ratio={vol_ratio}x). Risk: {garch_risk}.")

        return result

    except Exception as e:
        logger.error(f"GARCH fitting failed: {e}")
        return {"error": str(e)}