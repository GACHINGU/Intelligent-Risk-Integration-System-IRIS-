# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Signal Engine
#
# Translates all model outputs and the risk classification into
# a set of concrete, actionable POLICY SIGNALS.
#
# These signals are what the executive memorandum and dashboard
# display as the "what should be done" layer.
#
# Signal types:
#   RATE_ACTION    — what should the CBK do with interest rates?
#   MONITORING     — what should be watched closely?
#   COORDINATION   — what fiscal/structural actions are needed?
#   COMMUNICATION  — what should be communicated to markets/public?
#   RISK_FLAG      — specific risk conditions to be aware of
# ─────────────────────────────────────────────────────────────────────────────

from utils.logger import get_logger

logger = get_logger(__name__)


def generate_signals(classification: dict,
                     model_results:  dict,
                     latest:         dict,
                     iris_score_result: dict) -> dict:
    """
    Generate the full set of policy signals from IRIS outputs.

    INPUT:
        classification    — dict from risk.regime_classifier.classify()
        model_results     — dict from models.model_runner.run_all_models()
        latest            — latest indicator readings
        iris_score_result — dict from risk.score_builder.build_iris_score()

    OUTPUT: dict with categorised signals and priority actions
    """
    signals       = []
    iris_score    = classification.get("iris_score", 50)
    regime        = classification.get("regime", "MODERATE")
    inf_val       = latest.get("inflation",     {}).get("value")
    ir_val        = latest.get("interest_rate", {}).get("value")
    real_rate     = (ir_val - inf_val) if (ir_val and inf_val) else None

    vecm          = model_results.get("vecm",         {})
    garch         = model_results.get("garch",        {})
    regime_result = model_results.get("regime",       {})
    irf_result    = model_results.get("irf",          {})
    fevd          = model_results.get("fevd",         {})
    corr          = model_results.get("correlations", {})

    # ── RATE ACTION SIGNAL ─────────────────────────────────────────────────────
    if regime == "CRITICAL":
        signals.append({
            "type":     "RATE_ACTION",
            "priority": 1,
            "action":   "EMERGENCY TIGHTENING",
            "detail":   (
                "Immediate and significant interest rate increase required. "
                "IRIS score indicates crisis-level monetary conditions. "
                "Delay will entrench inflation expectations and extend the recovery timeline."
            ),
        })
    elif regime == "DANGER":
        signals.append({
            "type":     "RATE_ACTION",
            "priority": 1,
            "action":   "TIGHTEN",
            "detail":   (
                "Interest rate increase is recommended at the next MPC meeting. "
                "Inflation is above target and risk indicators are elevated. "
                f"Current real rate of {real_rate:.1f}% is insufficient protection for savers."
                if real_rate else
                "Rate increase recommended — inflation above target."
            ),
        })
    elif regime == "MODERATE":
        signals.append({
            "type":     "RATE_ACTION",
            "priority": 2,
            "action":   "WATCH AND PREPARE",
            "detail":   (
                "Hold current rate but prepare for tightening. "
                "Conditions are above target but not yet at crisis levels. "
                "A forward-looking rate adjustment in 1-2 MPC cycles is advisable "
                "if current trends continue."
            ),
        })
    else:   # STABLE
        signals.append({
            "type":     "RATE_ACTION",
            "priority": 3,
            "action":   "HOLD",
            "detail":   (
                "Maintain current policy rate. "
                "Inflation is within or near target. "
                "Monitor for emerging supply-side pressures."
            ),
        })

    # ── TRANSMISSION LAG SIGNAL ────────────────────────────────────────────────
    first_neg = irf_result.get("first_negative_year")
    if first_neg is not None:
        signals.append({
            "type":     "MONITORING",
            "priority": 2,
            "action":   "ACCOUNT FOR TRANSMISSION LAG",
            "detail":   (
                f"IRF analysis shows rate changes take approximately {first_neg} year(s) "
                f"to begin reducing inflation. "
                f"The MPC must act NOW for effects to materialise in {first_neg} year(s). "
                f"Do not wait for inflation to peak before acting."
            ),
        })

    # ── SUPPLY-SIDE SIGNAL ─────────────────────────────────────────────────────
    ir_share = fevd.get("ir_share_lr", 14)
    supply_share = 100 - ir_share
    signals.append({
        "type":     "COORDINATION",
        "priority": 2,
        "action":   "COORDINATE ON SUPPLY-SIDE",
        "detail":   (
            f"FEVD shows {supply_share:.0f}% of Kenya's inflation is supply-driven "
            f"(food, fuel, exchange rate) — outside the CBK's direct control. "
            f"Coordinate with National Treasury and Ministry of Agriculture on: "
            f"strategic grain reserves, fuel pricing policy, and exchange rate management."
        ),
    })

    # ── VOLATILITY PERSISTENCE SIGNAL ─────────────────────────────────────────
    persistence = garch.get("persistence", 0.5)
    garch_risk  = garch.get("garch_risk",  "UNKNOWN")
    if persistence > 0.8:
        signals.append({
            "type":     "RISK_FLAG",
            "priority": 2 if persistence < 0.95 else 1,
            "action":   "VOLATILITY PERSISTENCE WARNING",
            "detail":   (
                f"GARCH persistence = {persistence:.3f}. "
                f"Inflation volatility is slow to decay — once elevated, it tends to remain elevated. "
                f"The MPC should act pre-emptively. Waiting for volatility to self-resolve is not advised."
            ),
        })

    # ── REGIME TRANSITION SIGNAL ───────────────────────────────────────────────
    p_high        = regime_result.get("current_p_high",  0)
    p_low_to_high = regime_result.get("p_low_to_high",   0)
    p_high_to_low = regime_result.get("p_high_to_low",   0)

    if p_high < 0.5 and p_low_to_high > 0.25:
        signals.append({
            "type":     "RISK_FLAG",
            "priority": 2,
            "action":   "REGIME TRANSITION RISK",
            "detail":   (
                f"Kenya is currently in the LOW-INFLATION regime but "
                f"there is a {p_low_to_high*100:.0f}% probability of switching to "
                f"the HIGH-INFLATION regime next year. "
                f"Pre-emptive monitoring and policy preparation is advised."
            ),
        })
    elif p_high > 0.5:
        signals.append({
            "type":     "RISK_FLAG",
            "priority": 1,
            "action":   "HIGH-INFLATION REGIME ACTIVE",
            "detail":   (
                f"Kenya is in the HIGH-INFLATION regime (P={p_high*100:.0f}%). "
                f"Probability of remaining in this regime next year: {regime_result.get('p_stay_high', 0)*100:.0f}%. "
                f"Exit from the high-inflation regime typically requires sustained tightening."
            ),
        })

    # ── REACTIVE POLICY SIGNAL ─────────────────────────────────────────────────
    policy_char = vecm.get("policy_character", "REACTIVE")
    if policy_char == "REACTIVE":
        signals.append({
            "type":     "COMMUNICATION",
            "priority": 2,
            "action":   "SHIFT TO FORWARD-LOOKING FRAMEWORK",
            "detail":   (
                "VECM analysis confirms the CBK has historically been REACTIVE — "
                "adjusting rates AFTER inflation has already risen. "
                "The MPC should adopt a more forward-looking Taylor Rule-inspired framework, "
                "setting rates based on forecast inflation 2-3 years ahead rather than "
                "current inflation readings."
            ),
        })

    # ── FAN CHART COMMUNICATION SIGNAL ────────────────────────────────────────
    signals.append({
        "type":     "COMMUNICATION",
        "priority": 3,
        "action":   "PUBLISH INFLATION UNCERTAINTY BANDS",
        "detail":   (
            f"GARCH conditional volatility = {garch.get('current_vol', 'N/A')}. "
            f"The MPC should publish inflation fan charts (uncertainty bands) alongside "
            f"quarterly forecasts. This manages market expectations and builds CBK credibility. "
            f"Point forecasts alone understate the genuine uncertainty in the inflation outlook."
        ),
    })

    # ── FISHER EFFECT SIGNAL ───────────────────────────────────────────────────
    if not corr.get("fisher_holds", True):
        signals.append({
            "type":     "RISK_FLAG",
            "priority": 2,
            "action":   "MONETARY TRANSMISSION IMPAIRMENT",
            "detail":   (
                "The Fisher Effect has broken down — interest rates are not adjusting "
                "one-for-one with inflation as economic theory predicts. "
                "This indicates impaired monetary transmission, possibly due to: "
                "fiscal dominance, shallow credit markets, or large informal sector. "
                "Financial deepening policies should accompany rate adjustments."
            ),
        })

    # ── Sort by priority ───────────────────────────────────────────────────────
    signals.sort(key=lambda s: s["priority"])

    # ── Priority action (top signal) ───────────────────────────────────────────
    priority_action = signals[0] if signals else {}

    result = {
        "signals":         signals,
        "n_signals":       len(signals),
        "priority_action": priority_action,
        "regime":          regime,
        "iris_score":      iris_score,

        # Quick signal summary for dashboard header
        "rate_signal": next(
            (s["action"] for s in signals if s["type"] == "RATE_ACTION"),
            "HOLD"
        ),
        "top_risk_flag": next(
            (s["action"] for s in signals if s["type"] == "RISK_FLAG"),
            None
        ),
    }

    logger.info(
        f"Signals generated: {len(signals)} total. "
        f"Rate signal: {result['rate_signal']}. "
        f"Top risk: {result['top_risk_flag']}."
    )

    return result