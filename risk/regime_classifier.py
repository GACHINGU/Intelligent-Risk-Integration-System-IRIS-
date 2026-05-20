# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Regime Classifier
#
# Takes the IRIS Risk Score and model outputs and produces
# the final risk classification with full context:
#   - Risk level (Stable / Moderate / Danger / Critical)
#   - What conditions triggered this classification
#   - What the policy response should be
#   - Early warning flags
# ─────────────────────────────────────────────────────────────────────────────

from config.regimes import classify_regime, REGIME_DEFINITIONS
from utils.logger import get_logger

logger = get_logger(__name__)


def build_early_warnings(model_results: dict, latest: dict, iris_score: float) -> list:
    """
    Generate a list of specific early warning flags based on model outputs.
    Each flag is a dict with: flag, severity, plain_english.

    Severity levels: INFO, WARNING, ALERT, CRITICAL
    """
    warnings = []

    # ── Inflation above target ─────────────────────────────────────────────────
    inf_val = latest.get("inflation", {}).get("value")
    if inf_val is not None:
        if inf_val > 20:
            warnings.append({
                "flag":          "EXTREME_INFLATION",
                "severity":      "CRITICAL",
                "plain_english": f"Inflation at {inf_val:.1f}% — well above crisis threshold. "
                                 f"Comparable to Kenya's 1993 crisis levels.",
            })
        elif inf_val > 10:
            warnings.append({
                "flag":          "HIGH_INFLATION",
                "severity":      "ALERT",
                "plain_english": f"Inflation at {inf_val:.1f}% — significantly above CBK target band (2.5-7.5%). "
                                 f"Sustained action required.",
            })
        elif inf_val > 7.5:
            warnings.append({
                "flag":          "ABOVE_TARGET",
                "severity":      "WARNING",
                "plain_english": f"Inflation at {inf_val:.1f}% — above the CBK upper target of 7.5%. "
                                 f"Monitor closely.",
            })

    # ── Negative real interest rate ────────────────────────────────────────────
    ir_val = latest.get("interest_rate", {}).get("value")
    if inf_val is not None and ir_val is not None:
        real_rate = ir_val - inf_val
        if real_rate < -10:
            warnings.append({
                "flag":          "DEEPLY_NEGATIVE_REAL_RATE",
                "severity":      "CRITICAL",
                "plain_english": f"Real interest rate at {real_rate:.1f}% — deeply negative. "
                                 f"Savers are losing significant purchasing power. "
                                 f"Financial repression at crisis levels.",
            })
        elif real_rate < -5:
            warnings.append({
                "flag":          "NEGATIVE_REAL_RATE",
                "severity":      "ALERT",
                "plain_english": f"Real interest rate at {real_rate:.1f}%. "
                                 f"Inflation is outpacing bank returns — savers are losing value.",
            })
        elif real_rate < 0:
            warnings.append({
                "flag":          "MILDLY_NEGATIVE_REAL_RATE",
                "severity":      "WARNING",
                "plain_english": f"Real interest rate at {real_rate:.1f}%. "
                                 f"Interest rates are slightly below inflation — watch closely.",
            })

    # ── GARCH volatility warning ────────────────────────────────────────────────
    garch = model_results.get("garch", {})
    if garch and not garch.get("error"):
        vol_ratio = garch.get("vol_ratio", 1.0)
        if vol_ratio and vol_ratio > 2.0:
            warnings.append({
                "flag":          "EXTREME_VOLATILITY",
                "severity":      "CRITICAL",
                "plain_english": f"Inflation volatility is {vol_ratio:.1f}x above the historical average. "
                                 f"Comparable to Kenya's worst crisis periods. "
                                 f"Prices are highly unpredictable.",
            })
        elif vol_ratio and vol_ratio > 1.5:
            warnings.append({
                "flag":          "ELEVATED_VOLATILITY",
                "severity":      "ALERT",
                "plain_english": f"Inflation volatility is {vol_ratio:.1f}x above average. "
                                 f"Uncertainty is elevated — business and household planning is harder.",
            })

        persistence = garch.get("persistence", 0)
        if persistence > 0.95:
            warnings.append({
                "flag":          "HIGH_VOLATILITY_PERSISTENCE",
                "severity":      "WARNING",
                "plain_english": f"Inflation volatility persistence = {persistence:.3f}. "
                                 f"Once high volatility begins, it is very slow to resolve. "
                                 f"Early action is critical.",
            })

    # ── Regime warning ─────────────────────────────────────────────────────────
    regime = model_results.get("regime", {})
    if regime and not regime.get("error"):
        p_high = regime.get("current_p_high", 0)
        if p_high > 0.8:
            warnings.append({
                "flag":          "HIGH_INFLATION_REGIME_CONFIRMED",
                "severity":      "CRITICAL",
                "plain_english": f"P(high-inflation regime) = {p_high*100:.0f}%. "
                                 f"The system has entered crisis territory. "
                                 f"Immediate MPC action required.",
            })
        elif p_high > 0.5:
            warnings.append({
                "flag":          "HIGH_INFLATION_REGIME_ACTIVE",
                "severity":      "ALERT",
                "plain_english": f"P(high-inflation regime) = {p_high*100:.0f}%. "
                                 f"Kenya has crossed the regime threshold. "
                                 f"Tightening policy is advised.",
            })
        elif p_high > 0.35:
            warnings.append({
                "flag":          "REGIME_TRANSITION_RISK",
                "severity":      "WARNING",
                "plain_english": f"P(high-inflation regime) = {p_high*100:.0f}%. "
                                 f"Approaching the danger threshold. Monitor closely.",
            })

    # ── Fisher Effect breakdown ────────────────────────────────────────────────
    corr = model_results.get("correlations", {})
    if corr and not corr.get("error"):
        if not corr.get("fisher_holds", True):
            warnings.append({
                "flag":          "FISHER_EFFECT_BREAKDOWN",
                "severity":      "WARNING",
                "plain_english": "Interest rates are NOT moving one-for-one with inflation "
                                 "(Fisher Effect has broken down). "
                                 "Monetary policy transmission may be impaired.",
            })

    # ── IRIS score threshold warnings ──────────────────────────────────────────
    if iris_score >= 75:
        warnings.append({
            "flag":          "IRIS_CRITICAL_THRESHOLD",
            "severity":      "CRITICAL",
            "plain_english": f"IRIS composite risk score ({iris_score:.1f}) has entered CRITICAL territory. "
                             f"All risk indicators are flashing red simultaneously.",
        })
    elif iris_score >= 51:
        warnings.append({
            "flag":          "IRIS_DANGER_THRESHOLD",
            "severity":      "ALERT",
            "plain_english": f"IRIS composite risk score ({iris_score:.1f}) is in the DANGER zone. "
                             f"Multiple risk indicators require attention.",
        })

    # Sort by severity
    severity_order = {"CRITICAL": 0, "ALERT": 1, "WARNING": 2, "INFO": 3}
    warnings.sort(key=lambda w: severity_order.get(w["severity"], 4))

    return warnings


def classify(iris_score_result: dict,
             model_results: dict,
             latest: dict) -> dict:
    """
    Produce the full risk classification for IRIS.

    INPUT:
        iris_score_result — dict from risk.score_builder.build_iris_score()
        model_results     — dict from models.model_runner.run_all_models()
        latest            — dict with latest indicator readings

    OUTPUT: dict with full classification, warnings, and policy signals
    """
    iris_score    = iris_score_result.get("iris_score", 50)
    regime_def    = classify_regime(iris_score)
    early_warnings = build_early_warnings(model_results, latest, iris_score)

    # Count warnings by severity
    severity_counts = {"CRITICAL": 0, "ALERT": 0, "WARNING": 0, "INFO": 0}
    for w in early_warnings:
        sev = w.get("severity", "INFO")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    result = {
        # Core classification
        "iris_score":      iris_score,
        "regime":          regime_def["label"],
        "regime_emoji":    iris_score_result.get("regime_emoji",  "🟡"),
        "regime_colour":   iris_score_result.get("regime_colour", "#C5A028"),
        "urgency":         regime_def["urgency"],

        # Descriptions
        "description":     regime_def["description"],
        "plain_english":   regime_def["plain_english"],
        "policy_signal":   regime_def["policy_signal"],

        # Component scores
        "components":      iris_score_result.get("components", {}),
        "dominant_driver": iris_score_result.get("dominant_driver_label", ""),

        # Early warnings
        "early_warnings":     early_warnings,
        "n_critical_warnings": severity_counts["CRITICAL"],
        "n_alert_warnings":    severity_counts["ALERT"],
        "n_warnings":          severity_counts["WARNING"],

        # Conditions checklist
        "conditions":      regime_def["conditions"],

        # Summary one-liner
        "headline": (
            f"{iris_score_result.get('regime_emoji', '')} "
            f"IRIS Risk Score: {iris_score:.1f}/100 — "
            f"{regime_def['label']} | "
            f"{severity_counts['CRITICAL']} critical, "
            f"{severity_counts['ALERT']} alerts, "
            f"{severity_counts['WARNING']} warnings"
        ),
    }

    logger.info(
        f"Risk classification: {regime_def['label']} | "
        f"Score={iris_score:.1f} | "
        f"Warnings: {severity_counts}"
    )

    return result