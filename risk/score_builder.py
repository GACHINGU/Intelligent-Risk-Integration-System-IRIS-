# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Risk Score Builder
#
# WHAT IS THE IRIS RISK SCORE?
# A single number from 0 to 100 that aggregates ALL model outputs
# into one actionable signal.
#
#   0  - 25  = 🟢 STABLE
#   26 - 50  = 🟡 MODERATE
#   51 - 75  = 🟠 DANGER
#   76 - 100 = 🔴 CRITICAL
#
# HOW IS IT BUILT?
# We score each model output on a 0-100 scale, then take a
# weighted average. The weights reflect how much each model
# contributes to understanding Kenya's current monetary risk.
#
# COMPONENT WEIGHTS:
#   Inflation level      20%  — are we in the CBK target band?
#   Real interest rate   15%  — are savers being protected?
#   GARCH volatility     20%  — how unpredictable is inflation?
#   Regime probability   25%  — what does the regime model say?
#   VECM deviation       10%  — how far from long-run equilibrium?
#   Correlation signal    5%  — is the Fisher Effect breaking down?
#   FEVD supply risk      5%  — how supply-driven is inflation?
# ─────────────────────────────────────────────────────────────────────────────

import numpy as np
from config.settings import (
    CBK_INFLATION_TARGET_LOWER,
    CBK_INFLATION_TARGET_UPPER,
    CBK_INFLATION_TARGET_MID,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Component weights (must sum to 1.0) ───────────────────────────────────────
WEIGHTS = {
    "inflation_level":  0.20,
    "real_rate":        0.15,
    "garch_vol":        0.20,
    "regime_prob":      0.25,
    "vecm_deviation":   0.10,
    "correlation":      0.05,
    "fevd_supply":      0.05,
}


def score_inflation_level(latest: dict) -> float:
    """
    Score based on where current inflation sits relative to CBK target.

    0   = perfectly at 5% midpoint
    25  = at the edge of the target band (2.5% or 7.5%)
    50  = 5pp above target (12.5%)
    75  = 10pp above target (17.5%)
    100 = 20pp+ above target (crisis territory like 1993)
    """
    inf_val = latest.get("inflation", {}).get("value")
    if inf_val is None:
        return 50.0   # Unknown = assume moderate

    # Distance from target midpoint
    distance = abs(inf_val - CBK_INFLATION_TARGET_MID)

    if inf_val < CBK_INFLATION_TARGET_LOWER:
        # Below target — mild concern (deflation risk)
        score = min(distance * 5, 40)
    elif inf_val <= CBK_INFLATION_TARGET_UPPER:
        # Inside target band — low risk
        score = distance * 4
    else:
        # Above target band — score rises steeply
        excess = inf_val - CBK_INFLATION_TARGET_UPPER
        score  = 25 + min(excess * 5, 75)

    return round(min(max(score, 0), 100), 2)


def score_real_rate(latest: dict) -> float:
    """
    Score based on the real interest rate (nominal rate minus inflation).

    Positive real rate = savers protected = low risk
    Negative real rate = financial repression = higher risk

    0   = real rate > +5% (very positive)
    25  = real rate around 0%
    60  = real rate = -5%
    100 = real rate = -15% or worse
    """
    ir_val  = latest.get("interest_rate", {}).get("value")
    inf_val = latest.get("inflation",     {}).get("value")

    if ir_val is None or inf_val is None:
        return 40.0

    real_rate = ir_val - inf_val

    if real_rate >= 5:
        score = 5
    elif real_rate >= 2:
        score = 15
    elif real_rate >= 0:
        score = 25
    elif real_rate >= -3:
        score = 40
    elif real_rate >= -7:
        score = 60
    elif real_rate >= -12:
        score = 80
    else:
        score = 100

    return round(float(score), 2)


def score_garch_volatility(garch: dict) -> float:
    """
    Score based on GARCH conditional volatility relative to historical average.

    vol_ratio < 0.75  = below average volatility   → low score
    vol_ratio = 1.0   = at historical average       → moderate score
    vol_ratio > 1.5   = elevated volatility         → high score
    vol_ratio > 2.0   = crisis-level volatility     → very high score
    """
    if not garch or garch.get("error"):
        return 40.0

    vol_ratio = garch.get("vol_ratio")
    if vol_ratio is None:
        return 40.0

    if vol_ratio < 0.5:
        score = 5
    elif vol_ratio < 0.75:
        score = 15
    elif vol_ratio < 1.0:
        score = 30
    elif vol_ratio < 1.25:
        score = 45
    elif vol_ratio < 1.5:
        score = 60
    elif vol_ratio < 2.0:
        score = 75
    else:
        score = 90 + min((vol_ratio - 2.0) * 5, 10)

    # Also factor in persistence — high persistence = higher long-run risk
    persistence = garch.get("persistence", 0.5)
    persistence_bonus = max(0, (persistence - 0.8) * 50)   # adds up to 10 pts if persistence ~1.0

    return round(min(float(score) + persistence_bonus, 100), 2)


def score_regime_probability(regime: dict) -> float:
    """
    Score based on the Markov regime model's probability of
    being in the HIGH-INFLATION regime.

    P(high) = 0%   → score = 0
    P(high) = 50%  → score = 50
    P(high) = 80%  → score = 80
    P(high) = 100% → score = 100

    This is the most direct risk signal — we scale it linearly.
    """
    if not regime or regime.get("error"):
        return 40.0

    p_high = regime.get("current_p_high", 0.4)

    # Base score: linear on P(high)
    score = p_high * 100

    # Bonus for being in a persistent high-inflation regime
    p_stay_high = regime.get("p_stay_high", 0.5)
    if p_high > 0.5 and p_stay_high > 0.7:
        # We are in the high regime AND it is persistent — extra penalty
        persistence_bonus = (p_stay_high - 0.7) * 20
        score += persistence_bonus

    return round(min(float(score), 100), 2)


def score_vecm_deviation(vecm: dict, features_tail: dict) -> float:
    """
    Score based on how far the system is from its long-run equilibrium.

    Uses the real rate as a proxy for equilibrium deviation.
    The VECM alpha tells us how fast it corrects — slow correction = higher risk.

    This is a simplified proxy since computing the exact error correction
    term requires the full VECM fitted object.
    """
    if not vecm or vecm.get("error"):
        return 30.0

    # Real rate as proxy for deviation from Fisher equilibrium
    real_rate = features_tail.get("real_rate", 0)

    # Alpha (speed of correction) — lower absolute value = slower correction
    alpha_ir  = abs(vecm.get("alpha_ir",  0.3))
    alpha_inf = abs(vecm.get("alpha_inf", 0.2))

    # Slower correction = higher risk for same deviation
    correction_speed = (alpha_ir + alpha_inf) / 2
    slowness_factor  = max(0.5, 1.0 - correction_speed)  # 0.5 to 1.0

    if real_rate >= 5:
        base_score = 5
    elif real_rate >= 0:
        base_score = 20
    elif real_rate >= -5:
        base_score = 45
    elif real_rate >= -10:
        base_score = 65
    else:
        base_score = 85

    score = base_score * (1 + slowness_factor * 0.3)

    return round(min(float(score), 100), 2)


def score_correlation_signal(correlations: dict) -> float:
    """
    Score based on the current rolling correlation and Fisher Effect breakdown.

    Fisher Effect breakdown (slope != 1) suggests monetary policy
    is not transmitting normally — moderate risk signal.
    """
    if not correlations or correlations.get("error"):
        return 30.0

    score = 30.0   # neutral baseline

    # If Fisher Effect has broken down — moderate penalty
    if not correlations.get("fisher_holds", True):
        score += 20

    # If rolling correlation is trending in unexpected direction
    corr_trend = correlations.get("corr_trend", "STABLE")
    if corr_trend == "WEAKENING":
        score += 15   # Relationship between rates and inflation weakening
    elif corr_trend == "STRENGTHENING":
        score -= 10   # Strengthening = more predictable

    # Inflation leads rates by many years = very reactive CBK = higher risk
    peak_lag = correlations.get("peak_lag", 0)
    if peak_lag < -3:
        score += 15   # Inflation leading rates by > 3 years

    return round(min(max(float(score), 0), 100), 2)


def score_fevd_supply(fevd: dict) -> float:
    """
    Score based on how supply-driven inflation is.

    Higher supply-side share = monetary policy less effective = moderate risk.
    This is a structural signal — not an acute risk indicator.
    """
    if not fevd or fevd.get("error"):
        return 30.0

    ir_share = fevd.get("ir_share_lr", 14)   # % explained by CBK rates

    # Low IR share = supply-driven = rate hikes less effective
    if ir_share >= 40:
        score = 10    # Monetary policy is powerful — low structural risk
    elif ir_share >= 25:
        score = 25
    elif ir_share >= 15:
        score = 40
    elif ir_share >= 10:
        score = 55
    else:
        score = 70    # Almost all supply-driven — monetary policy very limited

    return round(float(score), 2)


def build_iris_score(model_results: dict,
                     latest: dict,
                     features_tail: dict) -> dict:
    """
    Build the composite IRIS Risk Score from all model outputs.

    INPUT:
        model_results — dict from model_runner.run_all_models()
        latest        — dict with latest inflation and interest_rate readings
        features_tail — dict of the most recent row of features DataFrame

    OUTPUT: dict with composite score, component scores, regime, and interpretation
    """
    logger.info("Building IRIS Risk Score...")

    # ── Compute component scores ───────────────────────────────────────────────
    components = {
        "inflation_level": score_inflation_level(latest),
        "real_rate":       score_real_rate(latest),
        "garch_vol":       score_garch_volatility(model_results.get("garch", {})),
        "regime_prob":     score_regime_probability(model_results.get("regime", {})),
        "vecm_deviation":  score_vecm_deviation(
                               model_results.get("vecm", {}),
                               features_tail,
                           ),
        "correlation":     score_correlation_signal(model_results.get("correlations", {})),
        "fevd_supply":     score_fevd_supply(model_results.get("fevd", {})),
    }

    # ── Weighted composite score ───────────────────────────────────────────────
    iris_score = sum(
        components[key] * WEIGHTS[key]
        for key in WEIGHTS
    )
    iris_score = round(iris_score, 2)

    # ── Classify regime ────────────────────────────────────────────────────────
    if iris_score <= 25:
        regime_label  = "STABLE"
        regime_emoji  = "🟢"
        regime_colour = "#006400"
        urgency       = "LOW"
    elif iris_score <= 50:
        regime_label  = "MODERATE"
        regime_emoji  = "🟡"
        regime_colour = "#C5A028"
        urgency       = "MEDIUM"
    elif iris_score <= 75:
        regime_label  = "DANGER"
        regime_emoji  = "🟠"
        regime_colour = "#E65100"
        urgency       = "HIGH"
    else:
        regime_label  = "CRITICAL"
        regime_emoji  = "🔴"
        regime_colour = "#8B0000"
        urgency       = "CRITICAL"

    # ── Dominant risk driver ───────────────────────────────────────────────────
    # Which component is contributing most to the risk score?
    weighted_contributions = {
        k: round(components[k] * WEIGHTS[k], 2)
        for k in WEIGHTS
    }
    dominant_driver = max(weighted_contributions, key=weighted_contributions.get)

    driver_labels = {
        "inflation_level": "Elevated inflation level",
        "real_rate":       "Negative real interest rate",
        "garch_vol":       "High inflation volatility",
        "regime_prob":     "High-inflation regime probability",
        "vecm_deviation":  "Deviation from long-run equilibrium",
        "correlation":     "Fisher Effect breakdown",
        "fevd_supply":     "Supply-driven inflation dominance",
    }

    result = {
        "iris_score":             iris_score,
        "regime_label":           regime_label,
        "regime_emoji":           regime_emoji,
        "regime_colour":          regime_colour,
        "urgency":                urgency,

        # Component breakdown
        "components":             components,
        "weighted_contributions": weighted_contributions,
        "dominant_driver":        dominant_driver,
        "dominant_driver_label":  driver_labels.get(dominant_driver, dominant_driver),

        # Summary plain English
        "summary": (
            f"IRIS Risk Score: {iris_score:.1f}/100 — {regime_emoji} {regime_label}. "
            f"Primary risk driver: {driver_labels.get(dominant_driver, dominant_driver)}. "
            f"Urgency level: {urgency}."
        ),
    }

    logger.info(
        f"IRIS Score: {iris_score:.1f}/100 | {regime_emoji} {regime_label} | "
        f"Dominant driver: {dominant_driver} ({weighted_contributions[dominant_driver]:.1f} pts)"
    )

    return result