# ─────────────────────────────────────────────────────────────────────────────
# IRIS — System Settings
# Central configuration file. All constants, thresholds, and parameters
# live here. Change something once here — it updates everywhere in the system.
# ─────────────────────────────────────────────────────────────────────────────

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ── API Configuration ─────────────────────────────────────────────────────────
TRADING_ECONOMICS_API_KEY = os.getenv("TRADING_ECONOMICS_API_KEY", "")

# Trading Economics indicator codes for Kenya
# These are the exact strings the TE API expects
TE_INDICATORS = {
    "inflation": "KEN/CPI YOY",          # Kenya CPI year-on-year inflation
    "interest_rate": "KEN/INTEREST RATE", # Kenya central bank interest rate
}

# ── App Metadata ──────────────────────────────────────────────────────────────
APP_TITLE   = "IRIS — Intelligent Risk Integration System"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "Kenya Monetary Policy Risk Intelligence"

# ── Data Settings ─────────────────────────────────────────────────────────────
HISTORICAL_START_YEAR = 1971
CACHE_EXPIRY_HOURS    = 1       # How long before we re-fetch from the API
REFRESH_INTERVAL_MIN  = 60      # Auto-refresh interval in minutes

# Historical data file paths
HISTORICAL_IR_PATH  = "data/historical/kenya_interest_rates.csv"
HISTORICAL_INF_PATH = "data/historical/kenya_inflation_data.csv"
CACHE_PATH          = "data/cache/"

# ── IRIS Risk Score Thresholds ────────────────────────────────────────────────
# The composite risk score runs from 0 (perfectly stable) to 100 (crisis)
RISK_THRESHOLDS = {
    "stable":   (0,  25),
    "moderate": (26, 50),
    "danger":   (51, 75),
    "critical": (76, 100),
}

RISK_LABELS = {
    "stable":   "🟢 STABLE",
    "moderate": "🟡 MODERATE",
    "danger":   "🟠 DANGER",
    "critical": "🔴 CRITICAL",
}

RISK_COLOURS = {
    "stable":   "#006400",   # CBK green
    "moderate": "#C5A028",   # Gold
    "danger":   "#E65100",   # Orange
    "critical": "#8B0000",   # Deep red
}

# ── Model Parameters ──────────────────────────────────────────────────────────
# VECM
VECM_MAX_LAGS      = 6      # Maximum lags to consider in lag selection
VECM_DETERMINISTIC = "ci"   # Constant inside cointegrating equation
VECM_SIGNIF        = 0.05   # Significance level for Johansen test

# IRF
IRF_PERIODS = 10            # How many years ahead to compute impulse responses

# FEVD
FEVD_PERIODS = 12           # How many years ahead to decompose forecast variance

# GARCH
GARCH_P = 1                 # GARCH lag order (p)
GARCH_Q = 1                 # ARCH lag order (q)
GARCH_DIST = "t"            # Error distribution — Student-t for fat tails

# Markov Regime-Switching
MARKOV_K_REGIMES = 2        # Number of regimes (low-vol and high-vol)
MARKOV_ORDER     = 1        # AR order inside each regime

# Rolling correlation window (years)
ROLLING_WINDOW = 10

# Cross-correlation max lag (years)
XCORR_MAX_LAG = 10

# ── CBK Policy Targets ────────────────────────────────────────────────────────
# These are the official CBK inflation target band
CBK_INFLATION_TARGET_LOWER = 2.5
CBK_INFLATION_TARGET_UPPER = 7.5
CBK_INFLATION_TARGET_MID   = 5.0

# ── Colour Palette (Kenya-inspired) ───────────────────────────────────────────
COLOURS = {
    "cbk_green":  "#006400",
    "cbk_dark":   "#003300",
    "cbk_light":  "#E8F5E9",
    "gold":       "#C5A028",
    "red":        "#8B0000",
    "orange":     "#E65100",
    "blue":       "#1565C0",
    "dark_grey":  "#1A1A1A",
    "mid_grey":   "#555555",
    "light_grey": "#F5F5F5",
    "white":      "#FFFFFF",
}