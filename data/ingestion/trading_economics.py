# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Live Data Ingestion
# Pulls Kenya's latest inflation and interest rate data
# from the Trading Economics API.
#
# Trading Economics provides real-time and historical macroeconomic data.
# Their API returns JSON — we parse it into clean pandas DataFrames.
#
# HOW IT WORKS:
#   1. We call the TE API with Kenya's indicator codes
#   2. We parse the JSON response into a clean DataFrame
#   3. We return the latest reading + recent history
#   4. If the API fails for any reason, we fall back to cached data
# ─────────────────────────────────────────────────────────────────────────────

import requests
import pandas as pd
from datetime import datetime
from config.settings import (
    TRADING_ECONOMICS_API_KEY,
    TE_INDICATORS,
)
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Base URL for Trading Economics API ────────────────────────────────────────
TE_BASE_URL = "https://api.tradingeconomics.com"


def fetch_indicator(indicator_code: str, start_date: str = "2000-01-01") -> pd.DataFrame:
    """
    Fetch a single macroeconomic indicator from Trading Economics.

    INPUT:
        indicator_code — the TE indicator string e.g. "KEN/CPI YOY"
        start_date     — how far back to pull history (YYYY-MM-DD)

    OUTPUT:
        A pandas DataFrame with columns:
            date        — datetime
            value       — float (the indicator value)
            indicator   — str (name of the indicator)
            country     — str (always 'Kenya')
        Returns empty DataFrame if the request fails.
    """
    if not TRADING_ECONOMICS_API_KEY:
        logger.error("No Trading Economics API key found. Check your .env file.")
        return pd.DataFrame()

    # Build the API URL
    # TE historical endpoint: /historical/country/{country}/indicator/{indicator}
    country   = "kenya"
    indicator = indicator_code.split("/")[1].lower().replace(" ", "%20")
    url = (
        f"{TE_BASE_URL}/historical/country/{country}"
        f"/indicator/{indicator}"
        f"?c={TRADING_ECONOMICS_API_KEY}"
        f"&f=json"
        f"&d1={start_date}"
    )

    logger.info(f"Fetching: {indicator_code} from Trading Economics...")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()   # Raises exception for 4xx/5xx errors
        data = response.json()

        if not data:
            logger.warning(f"Empty response for {indicator_code}")
            return pd.DataFrame()

        # Parse the JSON list into a DataFrame
        df = pd.DataFrame(data)

        # TE returns columns like: DateTime, Value, Country, Category etc.
        # We rename to our standard schema
        df = df.rename(columns={
            "DateTime": "date",
            "Value":    "value",
            "Country":  "country",
            "Category": "indicator",
        })

        # Keep only what we need
        cols = [c for c in ["date", "value", "country", "indicator"] if c in df.columns]
        df = df[cols].copy()

        # Parse date column
        df["date"] = pd.to_datetime(df["date"])

        # Drop rows with missing values
        df = df.dropna(subset=["value"])

        # Sort chronologically
        df = df.sort_values("date").reset_index(drop=True)

        logger.info(f"Fetched {len(df)} records for {indicator_code}. "
                    f"Latest: {df['date'].max().strftime('%Y-%m-%d')} = {df['value'].iloc[-1]:.2f}")

        return df

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {indicator_code}. API did not respond within 15 seconds.")
        return pd.DataFrame()

    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error fetching {indicator_code}. Check your internet connection.")
        return pd.DataFrame()

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching {indicator_code}: {e}")
        return pd.DataFrame()

    except Exception as e:
        logger.error(f"Unexpected error fetching {indicator_code}: {e}")
        return pd.DataFrame()


def fetch_latest_reading(indicator_code: str) -> dict:
    """
    Fetch just the single most recent reading for a given indicator.

    INPUT:  indicator_code — TE indicator string
    OUTPUT: dict with keys: value, date, indicator
            Returns None if fetch fails.
    """
    df = fetch_indicator(indicator_code)

    if df.empty:
        return None

    latest = df.iloc[-1]
    return {
        "value":     float(latest["value"]),
        "date":      latest["date"],
        "indicator": indicator_code,
    }


def fetch_all_kenya_indicators() -> dict:
    """
    Fetch ALL Kenya indicators that IRIS needs in one call.
    This is the main function called by the pipeline.

    OUTPUT: dict with keys:
        "inflation"      — DataFrame of Kenya CPI inflation history
        "interest_rate"  — DataFrame of Kenya interest rate history
        "latest"         — dict with the most recent reading for each
        "fetch_time"     — datetime when this fetch was completed
        "success"        — bool: True if both indicators fetched successfully
    """
    logger.info("=" * 55)
    logger.info("IRIS — Starting live data fetch from Trading Economics")
    logger.info("=" * 55)

    results = {
        "inflation":     pd.DataFrame(),
        "interest_rate": pd.DataFrame(),
        "latest":        {},
        "fetch_time":    datetime.now(),
        "success":       False,
    }

    # ── Fetch inflation ───────────────────────────────────────────────────────
    inf_df = fetch_indicator(TE_INDICATORS["inflation"])
    if not inf_df.empty:
        results["inflation"] = inf_df
        results["latest"]["inflation"] = {
            "value": float(inf_df["value"].iloc[-1]),
            "date":  inf_df["date"].iloc[-1],
        }
        logger.info(f"Inflation fetched. Latest: {results['latest']['inflation']['value']:.2f}%")
    else:
        logger.warning("Inflation fetch failed.")

    # ── Fetch interest rate ───────────────────────────────────────────────────
    ir_df = fetch_indicator(TE_INDICATORS["interest_rate"])
    if not ir_df.empty:
        results["interest_rate"] = ir_df
        results["latest"]["interest_rate"] = {
            "value": float(ir_df["value"].iloc[-1]),
            "date":  ir_df["date"].iloc[-1],
        }
        logger.info(f"Interest rate fetched. Latest: {results['latest']['interest_rate']['value']:.2f}%")
    else:
        logger.warning("Interest rate fetch failed.")

    # ── Determine overall success ─────────────────────────────────────────────
    results["success"] = (
        not results["inflation"].empty and
        not results["interest_rate"].empty
    )

    if results["success"]:
        logger.info("Live data fetch completed successfully.")
    else:
        logger.warning("Live data fetch partially or fully failed. Will use cached data.")

    return results