# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Auto Refresh Scheduler
#
# Manages automatic data refresh at configurable intervals.
# In Streamlit, we use st.cache_data TTL for primary refresh.
# This module handles the background refresh logic and
# tracks when the last refresh happened.
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
from datetime import datetime, timedelta
from config.settings import CACHE_PATH, REFRESH_INTERVAL_MIN
from utils.logger import get_logger

logger = get_logger(__name__)

REFRESH_STATE_FILE = os.path.join(CACHE_PATH, "refresh_state.json")
os.makedirs(CACHE_PATH, exist_ok=True)


def get_refresh_state() -> dict:
    """Load the current refresh state from disk."""
    try:
        if os.path.exists(REFRESH_STATE_FILE):
            with open(REFRESH_STATE_FILE) as f:
                state = json.load(f)
            state["last_refresh"] = datetime.fromisoformat(state["last_refresh"])
            return state
    except Exception:
        pass
    return {"last_refresh": datetime.min, "refresh_count": 0, "last_regime": None}


def save_refresh_state(state: dict):
    """Save refresh state to disk."""
    try:
        save_state = state.copy()
        if isinstance(save_state["last_refresh"], datetime):
            save_state["last_refresh"] = save_state["last_refresh"].isoformat()
        with open(REFRESH_STATE_FILE, "w") as f:
            json.dump(save_state, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save refresh state: {e}")


def should_refresh() -> bool:
    """
    Check whether a data refresh is due.
    Returns True if REFRESH_INTERVAL_MIN has elapsed since last refresh.
    """
    state    = get_refresh_state()
    now      = datetime.now()
    due_at   = state["last_refresh"] + timedelta(minutes=REFRESH_INTERVAL_MIN)
    is_due   = now >= due_at
    if is_due:
        logger.info(f"Refresh due. Last refresh: {state['last_refresh']}. "
                    f"Interval: {REFRESH_INTERVAL_MIN} min.")
    return is_due


def mark_refreshed(current_regime: str = None):
    """Mark that a refresh just completed."""
    state = get_refresh_state()
    state["last_refresh"]  = datetime.now()
    state["refresh_count"] = state.get("refresh_count", 0) + 1
    if current_regime:
        state["last_regime"] = current_regime
    save_refresh_state(state)
    logger.info(f"Refresh marked. Count: {state['refresh_count']}. "
                f"Next due in {REFRESH_INTERVAL_MIN} min.")


def minutes_until_next_refresh() -> float:
    """Return minutes until next scheduled refresh."""
    state  = get_refresh_state()
    due_at = state["last_refresh"] + timedelta(minutes=REFRESH_INTERVAL_MIN)
    delta  = (due_at - datetime.now()).total_seconds() / 60
    return max(0.0, round(delta, 1))


def get_refresh_summary() -> dict:
    """Return a summary of refresh status for the dashboard."""
    state = get_refresh_state()
    return {
        "last_refresh":         state["last_refresh"],
        "refresh_count":        state.get("refresh_count", 0),
        "minutes_until_next":   minutes_until_next_refresh(),
        "is_due":               should_refresh(),
        "last_regime":          state.get("last_regime"),
        "interval_minutes":     REFRESH_INTERVAL_MIN,
    }