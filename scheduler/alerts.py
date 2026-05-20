# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Alert System
#
# Detects significant changes between model runs and generates alerts.
# An alert is triggered when:
#   1. The IRIS Risk Score crosses a regime boundary
#   2. The Markov regime switches (low → high or high → low)
#   3. GARCH volatility spikes above a threshold
#   4. Inflation crosses the CBK target band
#   5. The real interest rate crosses zero
#
# Alerts are stored in a JSON file and displayed on the dashboard.
# In production, these could be sent via email or SMS.
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
from datetime import datetime
from config.settings import CACHE_PATH
from utils.logger import get_logger

logger = get_logger(__name__)

ALERTS_FILE = os.path.join(CACHE_PATH, "alerts.json")
os.makedirs(CACHE_PATH, exist_ok=True)

# Maximum alerts to keep in history
MAX_ALERTS = 50


def load_alerts() -> list:
    """Load stored alerts from disk."""
    try:
        if os.path.exists(ALERTS_FILE):
            with open(ALERTS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_alerts(alerts: list):
    """Save alerts to disk."""
    try:
        # Keep only the most recent MAX_ALERTS
        alerts = alerts[-MAX_ALERTS:]
        with open(ALERTS_FILE, "w") as f:
            json.dump(alerts, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Could not save alerts: {e}")


def _make_alert(alert_type: str, severity: str,
                title: str, detail: str,
                old_val=None, new_val=None) -> dict:
    """Create a new alert dict."""
    return {
        "id":         f"{alert_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "type":       alert_type,
        "severity":   severity,
        "title":      title,
        "detail":     detail,
        "old_value":  old_val,
        "new_value":  new_val,
        "timestamp":  datetime.now().isoformat(),
        "read":       False,
    }


def check_and_generate_alerts(current_iris: dict,
                               current_classification: dict,
                               current_models: dict,
                               current_latest: dict) -> list:
    """
    Compare current system state to previous state and generate alerts
    for significant changes.

    INPUT:
        current_iris           — current iris_score dict
        current_classification — current classification dict
        current_models         — current model_results dict
        current_latest         — current latest readings

    OUTPUT: list of new alert dicts generated in this run
    """
    new_alerts   = []
    stored_alerts = load_alerts()

    # Get previous state from last alert (if any)
    prev_regime = None
    prev_score  = None
    prev_p_high = None
    if stored_alerts:
        for alert in reversed(stored_alerts):
            if alert.get("type") == "REGIME_CHANGE" and prev_regime is None:
                prev_regime = alert.get("new_value")
            if alert.get("type") == "SCORE_CHANGE" and prev_score is None:
                prev_score = alert.get("new_value")

    current_regime  = current_iris.get("regime_label",    "MODERATE")
    current_score   = current_iris.get("iris_score",       50)
    current_p_high  = current_models.get("regime", {}).get("current_p_high", 0)
    inf_val         = current_latest.get("inflation",     {}).get("value")
    ir_val          = current_latest.get("interest_rate", {}).get("value")
    real_rate       = (ir_val - inf_val) if (inf_val and ir_val) else None
    garch_risk      = current_models.get("garch", {}).get("garch_risk", "MODERATE")
    vol_ratio       = current_models.get("garch", {}).get("vol_ratio",   1.0)

    # ── Alert 1: Regime boundary crossing ─────────────────────────────────────
    if prev_regime and prev_regime != current_regime:
        severity_map = {
            "STABLE → MODERATE":   "WARNING",
            "MODERATE → DANGER":   "ALERT",
            "DANGER → CRITICAL":   "CRITICAL",
            "CRITICAL → DANGER":   "INFO",
            "DANGER → MODERATE":   "INFO",
            "MODERATE → STABLE":   "INFO",
        }
        transition = f"{prev_regime} → {current_regime}"
        severity   = severity_map.get(transition, "WARNING")
        new_alerts.append(_make_alert(
            alert_type = "REGIME_CHANGE",
            severity   = severity,
            title      = f"IRIS Regime Change: {transition}",
            detail     = (
                f"The IRIS Risk Score has moved from {prev_regime} to {current_regime}. "
                f"Current score: {current_score:.1f}/100. "
                f"{'Immediate review of monetary policy stance is recommended.' if severity in ['ALERT', 'CRITICAL'] else 'Continue monitoring.'}"
            ),
            old_val = prev_regime,
            new_val = current_regime,
        ))
        logger.info(f"ALERT: Regime change {transition}")

    # ── Alert 2: Score crosses 50 (enters/exits danger zone) ──────────────────
    if prev_score is not None:
        if prev_score <= 50 < current_score:
            new_alerts.append(_make_alert(
                alert_type = "SCORE_CHANGE",
                severity   = "ALERT",
                title      = "IRIS Score Crossed 50 — Entered Danger Zone",
                detail     = (
                    f"IRIS score increased from {prev_score:.1f} to {current_score:.1f}, "
                    f"crossing the 50-point danger threshold. "
                    f"Multiple risk indicators are now elevated simultaneously."
                ),
                old_val = prev_score,
                new_val = current_score,
            ))
        elif prev_score > 50 >= current_score:
            new_alerts.append(_make_alert(
                alert_type = "SCORE_CHANGE",
                severity   = "INFO",
                title      = "IRIS Score Dropped Below 50 — Exited Danger Zone",
                detail     = (
                    f"IRIS score decreased from {prev_score:.1f} to {current_score:.1f}. "
                    f"Risk conditions are improving."
                ),
                old_val = prev_score,
                new_val = current_score,
            ))

    # ── Alert 3: Inflation crosses target band ─────────────────────────────────
    if inf_val is not None:
        if inf_val > 15:
            new_alerts.append(_make_alert(
                alert_type = "INFLATION_EXTREME",
                severity   = "CRITICAL",
                title      = f"Extreme Inflation: {inf_val:.1f}%",
                detail     = (
                    f"Inflation has reached {inf_val:.1f}% — well above the crisis threshold. "
                    f"Comparable to Kenya's 1993 conditions. Immediate policy response required."
                ),
                new_val = inf_val,
            ))
        elif inf_val > 10:
            new_alerts.append(_make_alert(
                alert_type = "INFLATION_HIGH",
                severity   = "ALERT",
                title      = f"High Inflation Alert: {inf_val:.1f}%",
                detail     = (
                    f"Inflation at {inf_val:.1f}% is significantly above the CBK target band. "
                    f"Sustained corrective action is required."
                ),
                new_val = inf_val,
            ))

    # ── Alert 4: Real rate crosses zero ───────────────────────────────────────
    if real_rate is not None and real_rate < -5:
        new_alerts.append(_make_alert(
            alert_type = "NEGATIVE_REAL_RATE",
            severity   = "ALERT",
            title      = f"Significantly Negative Real Rate: {real_rate:.2f}%",
            detail     = (
                f"Real interest rate at {real_rate:.2f}%. "
                f"Savers are losing significant purchasing power. "
                f"Financial repression is at a concerning level."
            ),
            new_val = real_rate,
        ))

    # ── Alert 5: GARCH volatility spike ───────────────────────────────────────
    if vol_ratio is not None and vol_ratio > 1.75:
        new_alerts.append(_make_alert(
            alert_type = "VOLATILITY_SPIKE",
            severity   = "ALERT" if vol_ratio < 2.5 else "CRITICAL",
            title      = f"Inflation Volatility Spike: {vol_ratio:.2f}x historical average",
            detail     = (
                f"GARCH conditional volatility has risen to {vol_ratio:.2f}x the historical average. "
                f"Inflation has become significantly harder to predict. "
                f"Household and business planning is materially impaired."
            ),
            new_val = vol_ratio,
        ))

    # ── Alert 6: Regime probability threshold ─────────────────────────────────
    if current_p_high > 0.75:
        new_alerts.append(_make_alert(
            alert_type = "REGIME_PROBABILITY",
            severity   = "CRITICAL" if current_p_high > 0.9 else "ALERT",
            title      = f"High-Inflation Regime: P(high) = {current_p_high*100:.0f}%",
            detail     = (
                f"The Markov regime model estimates a {current_p_high*100:.0f}% probability "
                f"of being in the high-inflation regime. "
                f"Decisive policy action is recommended to prevent regime entrenchment."
            ),
            new_val = current_p_high,
        ))

    # Save current score for next comparison
    if current_score != prev_score:
        new_alerts.append(_make_alert(
            alert_type = "SCORE_CHANGE",
            severity   = "INFO",
            title      = f"IRIS Score Updated: {current_score:.1f}/100",
            detail     = f"IRIS composite risk score updated to {current_score:.1f}/100 ({current_regime}).",
            old_val    = prev_score,
            new_val    = current_score,
        ))

    # Persist new alerts
    all_alerts = stored_alerts + new_alerts
    save_alerts(all_alerts)

    if new_alerts:
        logger.info(f"{len(new_alerts)} new alert(s) generated.")

    return new_alerts


def get_unread_alerts() -> list:
    """Return all unread alerts, most recent first."""
    alerts = load_alerts()
    return [a for a in reversed(alerts) if not a.get("read", False)]


def mark_all_read():
    """Mark all alerts as read."""
    alerts = load_alerts()
    for a in alerts:
        a["read"] = True
    save_alerts(alerts)


def get_alert_summary() -> dict:
    """Return a summary of current alert status."""
    alerts   = load_alerts()
    unread   = [a for a in alerts if not a.get("read", False)]
    critical = [a for a in unread if a.get("severity") == "CRITICAL"]
    alert_l  = [a for a in unread if a.get("severity") == "ALERT"]
    warning  = [a for a in unread if a.get("severity") == "WARNING"]
    return {
        "total_alerts":     len(alerts),
        "unread_count":     len(unread),
        "critical_count":   len(critical),
        "alert_count":      len(alert_l),
        "warning_count":    len(warning),
        "latest_alert":     unread[-1] if unread else None,
        "has_critical":     len(critical) > 0,
    }