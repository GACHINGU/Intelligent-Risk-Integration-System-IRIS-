# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Regime Definitions
# Defines what each risk regime means, what triggers it,
# and what the recommended policy response is.
# ─────────────────────────────────────────────────────────────────────────────

REGIME_DEFINITIONS = {

    "stable": {
        "label":       "STABLE",
        "emoji":       "🟢",
        "score_range": (0, 25),
        "colour":      "#006400",

        # What the data looks like in this regime
        "description": (
            "Inflation is within or close to the CBK target band (2.5%-7.5%). "
            "Interest rates are providing positive real returns to savers. "
            "Volatility is low and predictable. "
            "The economy is in a low-risk monetary environment."
        ),

        # Plain English for the wananchi brief
        "plain_english": (
            "Prices are rising at a manageable rate. "
            "Your savings in the bank are roughly holding their value. "
            "This is the environment the CBK aims to maintain."
        ),

        # Typical conditions that define this regime
        "conditions": [
            "Inflation between 2.5% and 7.5%",
            "Positive real interest rate (rate > inflation)",
            "GARCH volatility below historical average",
            "Markov regime probability: low-inflation regime > 70%",
            "Correlation stable and within expected range",
        ],

        # What the MPC should do
        "policy_signal": "HOLD — maintain current policy stance. Monitor for emerging risks.",

        # Urgency level for the memorandum
        "urgency": "LOW",
    },

    "moderate": {
        "label":       "MODERATE",
        "emoji":       "🟡",
        "score_range": (26, 50),
        "colour":      "#C5A028",

        "description": (
            "Inflation is above the CBK target band or trending upward. "
            "Real interest rates may be turning negative. "
            "Volatility is rising but not yet at crisis levels. "
            "The system is under mild stress — early action advised."
        ),

        "plain_english": (
            "Prices are rising faster than ideal. "
            "If you have savings, they may be losing a little value in real terms. "
            "The CBK is likely watching this closely and may act soon."
        ),

        "conditions": [
            "Inflation between 7.5% and 15%",
            "Real interest rate approaching zero or slightly negative",
            "GARCH volatility rising toward or above historical average",
            "Markov regime probability: high-inflation regime 30%-60%",
            "Rolling correlation shifting — structural change possible",
        ],

        "policy_signal": "WATCH — consider gradual tightening. Increase monitoring frequency.",

        "urgency": "MEDIUM",
    },

    "danger": {
        "label":       "DANGER",
        "emoji":       "🟠",
        "score_range": (51, 75),
        "colour":      "#E65100",

        "description": (
            "Inflation is significantly above target and accelerating. "
            "Real interest rates are materially negative — savers are losing purchasing power. "
            "Volatility is high and persistent. "
            "A regime shift to the crisis mode is probable without intervention."
        ),

        "plain_english": (
            "Prices are rising significantly and your money is losing value in the bank. "
            "This is the kind of environment where everyday costs — unga, transport, rent — "
            "start feeling noticeably heavier. The CBK needs to act."
        ),

        "conditions": [
            "Inflation between 15% and 30%",
            "Real interest rate clearly negative (rate minus inflation < -5%)",
            "GARCH volatility significantly above historical average",
            "Markov regime probability: high-inflation regime > 60%",
            "Cointegration weakening — long-run anchor under stress",
        ],

        "policy_signal": "ACT — recommend rate increase. Coordinate with Treasury on supply-side measures.",

        "urgency": "HIGH",
    },

    "critical": {
        "label":       "CRITICAL",
        "emoji":       "🔴",
        "score_range": (76, 100),
        "colour":      "#8B0000",

        "description": (
            "Kenya is in or approaching a monetary crisis. "
            "Inflation is at extreme levels. Real interest rates are deeply negative. "
            "Volatility is at or near crisis peaks (comparable to 1993, 2008). "
            "Immediate, decisive policy action is required. "
            "The risk of permanent damage to monetary credibility is real."
        ),

        "plain_english": (
            "This is a serious situation. Prices are rising so fast that "
            "ordinary Kenyans are struggling to keep up with basic costs. "
            "The last time Kenya was here was 1993 — when unga prices nearly doubled in one year. "
            "Urgent government and CBK action is needed now."
        ),

        "conditions": [
            "Inflation above 30%",
            "Real interest rate deeply negative (rate minus inflation < -10%)",
            "GARCH volatility at or near historical crisis peaks",
            "Markov regime probability: high-inflation regime > 80%",
            "Cointegration broken — long-run monetary anchor has failed",
        ],

        "policy_signal": "EMERGENCY — immediate and decisive rate action required. Escalate to Governor and MPC.",

        "urgency": "CRITICAL",
    },
}


def classify_regime(iris_score: float) -> dict:
    """
    Given an IRIS Risk Score (0-100), return the full regime definition.

    INPUT:  iris_score — float between 0 and 100
    OUTPUT: dict with regime label, colour, description, policy signal, etc.
    """
    if iris_score <= 25:
        return REGIME_DEFINITIONS["stable"]
    elif iris_score <= 50:
        return REGIME_DEFINITIONS["moderate"]
    elif iris_score <= 75:
        return REGIME_DEFINITIONS["danger"]
    else:
        return REGIME_DEFINITIONS["critical"]