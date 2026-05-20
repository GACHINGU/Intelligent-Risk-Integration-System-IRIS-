# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Model Runner (Orchestrator)
#
# This is the conductor of the orchestra.
# It runs ALL models in the correct sequence on a single dataset
# and returns a unified results dict that the rest of IRIS consumes.
#
# SEQUENCE:
#   1. Stationarity   — ADF + KPSS on both series
#   2. Cointegration  — Johansen test → determines VECM vs VAR
#   3. VECM           — fitted using Johansen rank
#   4. IRF            — impulse responses from fitted VECM
#   5. FEVD           — variance decomposition from companion VAR
#   6. GARCH          — volatility model on inflation
#   7. Regime         — Markov switching on inflation
#   8. Correlations   — all correlation measures
#
# OUTPUT:
#   A single dict — model_results — that every other module reads from.
#   This dict flows into: risk engine, memo generator, dashboard.
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
from datetime import datetime

from models.stationarity      import run_all_stationarity
from models.cointegration     import run_johansen
from models.vecm              import run_vecm
from models.irf               import run_irf
from models.fevd              import run_fevd
from models.garch             import run_garch
from models.regime_switching  import run_regime_switching
from models.correlations      import run_correlations
from config.settings          import VECM_MAX_LAGS, IRF_PERIODS, FEVD_PERIODS

from utils.logger import get_logger

logger = get_logger(__name__)


def run_all_models(df: pd.DataFrame) -> dict:
    """
    Run the full IRIS model stack on the prepared annual DataFrame.

    INPUT:  df — annual DataFrame from data pipeline (features included)
    OUTPUT: dict with all model results, timestamps, and a status summary
    """
    logger.info("=" * 60)
    logger.info("IRIS MODEL RUNNER — Starting full model stack")
    logger.info("=" * 60)

    start_time = datetime.now()
    results    = {
        "run_time":      start_time,
        "n_obs":         len(df),
        "year_range":    f"{int(df['year'].min())} - {int(df['year'].max())}",
        "status":        {},
        "errors":        [],
    }

    # ── 1. Stationarity ───────────────────────────────────────────────────────
    logger.info("[1/8] Running stationarity tests...")
    try:
        results["stationarity"] = run_all_stationarity(df)
        results["status"]["stationarity"] = "OK"
        logger.info("      Stationarity: OK")
    except Exception as e:
        results["stationarity"] = {}
        results["status"]["stationarity"] = f"ERROR: {e}"
        results["errors"].append(f"Stationarity: {e}")
        logger.error(f"      Stationarity FAILED: {e}")

    # ── 2. Cointegration ──────────────────────────────────────────────────────
    logger.info("[2/8] Running Johansen cointegration test...")
    try:
        results["cointegration"] = run_johansen(df)
        results["status"]["cointegration"] = "OK"
        coint_rank = results["cointegration"].get("rank", 1)
        logger.info(f"      Cointegration: OK. Rank={coint_rank}")
    except Exception as e:
        results["cointegration"] = {"rank": 1, "cointegrated": True}
        coint_rank = 1
        results["status"]["cointegration"] = f"ERROR: {e}"
        results["errors"].append(f"Cointegration: {e}")
        logger.error(f"      Cointegration FAILED: {e}")

    # ── 3. VECM ───────────────────────────────────────────────────────────────
    logger.info("[3/8] Fitting VECM...")
    try:
        results["vecm"] = run_vecm(
            df,
            coint_rank=max(1, coint_rank),
            k_ar_diff=1,
        )
        results["status"]["vecm"] = "OK"
        logger.info("      VECM: OK")
    except Exception as e:
        results["vecm"] = {}
        results["status"]["vecm"] = f"ERROR: {e}"
        results["errors"].append(f"VECM: {e}")
        logger.error(f"      VECM FAILED: {e}")

    # ── 4. IRF ────────────────────────────────────────────────────────────────
    logger.info("[4/8] Computing Impulse Response Functions...")
    try:
        results["irf"] = run_irf(
            results["vecm"],
            periods=IRF_PERIODS,
        )
        results["status"]["irf"] = "OK"
        logger.info("      IRF: OK")
    except Exception as e:
        results["irf"] = {}
        results["status"]["irf"] = f"ERROR: {e}"
        results["errors"].append(f"IRF: {e}")
        logger.error(f"      IRF FAILED: {e}")

    # ── 5. FEVD ───────────────────────────────────────────────────────────────
    logger.info("[5/8] Computing FEVD...")
    try:
        results["fevd"] = run_fevd(df, periods=FEVD_PERIODS)
        results["status"]["fevd"] = "OK"
        logger.info("      FEVD: OK")
    except Exception as e:
        results["fevd"] = {}
        results["status"]["fevd"] = f"ERROR: {e}"
        results["errors"].append(f"FEVD: {e}")
        logger.error(f"      FEVD FAILED: {e}")

    # ── 6. GARCH ──────────────────────────────────────────────────────────────
    logger.info("[6/8] Fitting GARCH volatility model...")
    try:
        results["garch"] = run_garch(df)
        results["status"]["garch"] = "OK"
        logger.info("      GARCH: OK")
    except Exception as e:
        results["garch"] = {}
        results["status"]["garch"] = f"ERROR: {e}"
        results["errors"].append(f"GARCH: {e}")
        logger.error(f"      GARCH FAILED: {e}")

    # ── 7. Regime Switching ───────────────────────────────────────────────────
    logger.info("[7/8] Fitting Markov Regime-Switching model...")
    try:
        results["regime"] = run_regime_switching(df)
        results["status"]["regime"] = "OK"
        logger.info("      Regime Switching: OK")
    except Exception as e:
        results["regime"] = {}
        results["status"]["regime"] = f"ERROR: {e}"
        results["errors"].append(f"Regime: {e}")
        logger.error(f"      Regime Switching FAILED: {e}")

    # ── 8. Correlations ───────────────────────────────────────────────────────
    logger.info("[8/8] Computing correlation analysis...")
    try:
        results["correlations"] = run_correlations(df)
        results["status"]["correlations"] = "OK"
        logger.info("      Correlations: OK")
    except Exception as e:
        results["correlations"] = {}
        results["status"]["correlations"] = f"ERROR: {e}"
        results["errors"].append(f"Correlations: {e}")
        logger.error(f"      Correlations FAILED: {e}")

    # ── Summary ───────────────────────────────────────────────────────────────
    elapsed   = (datetime.now() - start_time).seconds
    n_ok      = sum(1 for v in results["status"].values() if v == "OK")
    n_total   = len(results["status"])
    n_errors  = len(results["errors"])

    results["elapsed_seconds"] = elapsed
    results["models_ok"]       = n_ok
    results["models_total"]    = n_total
    results["all_models_ok"]   = n_errors == 0

    logger.info("=" * 60)
    logger.info(f"IRIS MODEL RUNNER — Complete in {elapsed}s. "
                f"{n_ok}/{n_total} models succeeded.")
    if results["errors"]:
        logger.warning(f"Errors: {results['errors']}")
    logger.info("=" * 60)

    return results