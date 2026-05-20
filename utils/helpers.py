# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Shared Helpers
# Utility functions used across the system.
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


def safe_float(val, fallback=None):
    """Safely convert a value to float."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return fallback


def safe_format(val, fmt=".2f", fallback="N/A", suffix=""):
    """Safely format a number with a suffix."""
    try:
        return format(float(val), fmt) + suffix
    except (TypeError, ValueError):
        return fallback


def pct(val, fallback="N/A"):
    """Format as percentage."""
    return safe_format(val, ".2f", fallback, "%")


def get_latest_from_features(features: pd.DataFrame) -> dict:
    """
    Extract the latest readings from the features DataFrame.
    Used when API is unavailable.
    """
    if features is None or features.empty:
        return {}
    last = features.iloc[-1]
    return {
        "inflation": {
            "value": safe_float(last.get("inflation")),
            "date":  str(int(last.get("year", 0))),
        },
        "interest_rate": {
            "value": safe_float(last.get("interest_rate")),
            "date":  str(int(last.get("year", 0))),
        },
    }


def calculate_real_rate(ir_val, inf_val):
    """Calculate real interest rate. Returns None if inputs invalid."""
    try:
        return float(ir_val) - float(inf_val)
    except (TypeError, ValueError):
        return None


def classify_real_rate(real_rate):
    """Return a plain-English label for the real rate level."""
    if real_rate is None:
        return "Unknown"
    if real_rate >= 5:
        return "Very positive — strong saver protection"
    elif real_rate >= 2:
        return "Positive — adequate saver protection"
    elif real_rate >= 0:
        return "Marginally positive — minimal protection"
    elif real_rate >= -3:
        return "Mildly negative — mild financial repression"
    elif real_rate >= -7:
        return "Negative — significant financial repression"
    else:
        return "Deeply negative — severe financial repression"


def percentile_rank(series: pd.Series, value: float) -> float:
    """Return percentile rank of a value within a series (0-100)."""
    try:
        return float((series < value).mean() * 100)
    except Exception:
        return 50.0


def find_similar_years(features: pd.DataFrame,
                        inf_val: float,
                        ir_val:  float,
                        top_n:   int = 5) -> pd.DataFrame:
    """
    Find historical years with conditions most similar to current.
    Uses Euclidean distance on inflation and interest rate.
    """
    if features is None or features.empty:
        return pd.DataFrame()
    df = features.copy()
    df["distance"] = np.sqrt(
        (df["inflation"]     - inf_val) ** 2 +
        (df["interest_rate"] - ir_val)  ** 2
    )
    cols = ["year", "inflation", "interest_rate", "real_rate", "distance"]
    cols = [c for c in cols if c in df.columns]
    return df.nsmallest(top_n, "distance")[cols].round(3)


def era_label(year: int) -> str:
    """Return the historical era label for a given year."""
    if year <= 1990:
        return "Financial Repression Era (1971-1990)"
    elif year <= 2003:
        return "Crisis Era (1991-2003)"
    elif year <= 2013:
        return "Reform Era (2004-2013)"
    else:
        return "Modern Era (2014-present)"


def regime_colour(regime_label: str) -> str:
    """Return hex colour for a regime label."""
    return {
        "STABLE":   "#006400",
        "MODERATE": "#C5A028",
        "DANGER":   "#E65100",
        "CRITICAL": "#8B0000",
    }.get(regime_label.upper(), "#555555")


def urgency_emoji(urgency: str) -> str:
    """Return emoji for urgency level."""
    return {
        "LOW":      "🟢",
        "MEDIUM":   "🟡",
        "HIGH":     "🟠",
        "CRITICAL": "🔴",
    }.get(urgency.upper(), "⚪")


def format_number_kenyan(value: float, currency: bool = False) -> str:
    """
    Format a number in Kenyan style with commas.
    e.g. 1000000 → 'KES 1,000,000' or '1,000,000'
    """
    try:
        formatted = f"{float(value):,.2f}"
        return f"KES {formatted}" if currency else formatted
    except (TypeError, ValueError):
        return "N/A"


def months_since(date_str: str) -> int:
    """Return months elapsed since a date string (YYYY or YYYY-MM-DD)."""
    try:
        if len(str(date_str)) == 4:
            past = datetime(int(date_str), 1, 1)
        else:
            past = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
        delta = datetime.now() - past
        return int(delta.days / 30)
    except Exception:
        return 0