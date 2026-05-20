# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Data Cache
#
# WHY CACHING?
# The Trading Economics API has rate limits and costs per call.
# We do not want to re-fetch data every time the dashboard refreshes.
# Instead, we save the last successful fetch to disk and only re-fetch
# when the cache has expired (default: 1 hour).
#
# Think of it like this:
#   Without cache: every page refresh = new API call = slow + expensive
#   With cache:    first call fetches, all others use saved copy until expired
#
# Cache files are stored as CSV in data/cache/
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from config.settings import CACHE_PATH, CACHE_EXPIRY_HOURS
from utils.logger import get_logger

logger = get_logger(__name__)

# Create cache directory if it does not exist
os.makedirs(CACHE_PATH, exist_ok=True)

# File paths for each cached item
CACHE_FILES = {
    "inflation":     os.path.join(CACHE_PATH, "inflation.csv"),
    "interest_rate": os.path.join(CACHE_PATH, "interest_rate.csv"),
    "metadata":      os.path.join(CACHE_PATH, "metadata.json"),
}


def save_to_cache(data: dict) -> bool:
    """
    Save fetched data to disk cache.

    INPUT:  data — the dict returned by fetch_all_kenya_indicators()
    OUTPUT: True if saved successfully, False otherwise
    """
    try:
        # Save each DataFrame as CSV
        if not data["inflation"].empty:
            data["inflation"].to_csv(CACHE_FILES["inflation"], index=False)

        if not data["interest_rate"].empty:
            data["interest_rate"].to_csv(CACHE_FILES["interest_rate"], index=False)

        # Save metadata (fetch time and latest values)
        metadata = {
            "fetch_time": data["fetch_time"].isoformat(),
            "latest": {
                k: {
                    "value": v["value"],
                    "date":  v["date"].isoformat() if hasattr(v["date"], "isoformat") else str(v["date"]),
                }
                for k, v in data.get("latest", {}).items()
            },
            "success": data.get("success", False),
        }
        with open(CACHE_FILES["metadata"], "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Data saved to cache at {CACHE_PATH}")
        return True

    except Exception as e:
        logger.error(f"Failed to save cache: {e}")
        return False


def load_from_cache() -> dict:
    """
    Load previously cached data from disk.

    OUTPUT: dict in the same format as fetch_all_kenya_indicators()
            Returns None if cache does not exist or cannot be read.
    """
    try:
        # Check metadata file exists
        if not os.path.exists(CACHE_FILES["metadata"]):
            logger.info("No cache metadata found.")
            return None

        # Load metadata
        with open(CACHE_FILES["metadata"], "r") as f:
            metadata = json.load(f)

        # Load DataFrames
        inf_df = pd.DataFrame()
        ir_df  = pd.DataFrame()

        if os.path.exists(CACHE_FILES["inflation"]):
            inf_df = pd.read_csv(CACHE_FILES["inflation"], parse_dates=["date"])

        if os.path.exists(CACHE_FILES["interest_rate"]):
            ir_df = pd.read_csv(CACHE_FILES["interest_rate"], parse_dates=["date"])

        # Reconstruct latest dict with proper types
        latest = {}
        for k, v in metadata.get("latest", {}).items():
            latest[k] = {
                "value": v["value"],
                "date":  pd.to_datetime(v["date"]),
            }

        cached = {
            "inflation":     inf_df,
            "interest_rate": ir_df,
            "latest":        latest,
            "fetch_time":    datetime.fromisoformat(metadata["fetch_time"]),
            "success":       metadata.get("success", False),
        }

        logger.info(f"Cache loaded. Originally fetched at: {cached['fetch_time']}")
        return cached

    except Exception as e:
        logger.error(f"Failed to load cache: {e}")
        return None


def is_cache_valid() -> bool:
    """
    Check whether the cache is still fresh (within CACHE_EXPIRY_HOURS).

    OUTPUT: True if cache exists and is not expired. False otherwise.
    """
    if not os.path.exists(CACHE_FILES["metadata"]):
        return False

    try:
        with open(CACHE_FILES["metadata"], "r") as f:
            metadata = json.load(f)

        fetch_time = datetime.fromisoformat(metadata["fetch_time"])
        expiry     = fetch_time + timedelta(hours=CACHE_EXPIRY_HOURS)
        now        = datetime.now()

        if now < expiry:
            remaining = (expiry - now).seconds // 60
            logger.info(f"Cache is valid. Expires in {remaining} minutes.")
            return True
        else:
            logger.info("Cache has expired. Will re-fetch from API.")
            return False

    except Exception as e:
        logger.error(f"Error checking cache validity: {e}")
        return False


def get_cache_age_minutes() -> float:
    """
    Return how many minutes ago the cache was last updated.
    Returns None if no cache exists.
    """
    if not os.path.exists(CACHE_FILES["metadata"]):
        return None

    try:
        with open(CACHE_FILES["metadata"], "r") as f:
            metadata = json.load(f)

        fetch_time = datetime.fromisoformat(metadata["fetch_time"])
        age_minutes = (datetime.now() - fetch_time).seconds / 60
        return round(age_minutes, 1)

    except Exception:
        return None