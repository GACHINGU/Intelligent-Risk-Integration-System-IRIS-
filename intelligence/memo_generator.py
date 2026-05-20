# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Memo Generator (Orchestrator)
#
# Builds all four memo types from model outputs + narrative engine:
#   1. Governor Memo     — technical, formal, strategic
#   2. MPC Memo          — operational, specific recommendations
#   3. Treasury Memo     — fiscal coordination, supply-side
#   4. Wananchi Brief    — plain English, relatable, Kenyan examples
#
# Each memo is a structured dict that can be:
#   - Rendered in the Streamlit dashboard
#   - Exported as PDF via utils/exporter.py
#   - Stored for audit trail
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime
from intelligence.narrative_engine import build_full_narrative
from intelligence.templates.governor_memo   import build_governor_memo
from intelligence.templates.mpc_memo        import build_mpc_memo
from intelligence.templates.wananchi_brief  import build_wananchi_brief
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_all_memos(model_results:  dict,
                        latest:         dict,
                        iris_score:     dict,
                        classification: dict,
                        signals:        dict,
                        features_tail:  dict) -> dict:
    """
    Generate all four memo types from IRIS outputs.

    INPUT:
        model_results  — from model_runner.run_all_models()
        latest         — latest indicator readings
        iris_score     — from score_builder.build_iris_score()
        classification — from regime_classifier.classify()
        signals        — from signal_engine.generate_signals()
        features_tail  — most recent feature row as dict

    OUTPUT: dict with four memos keyed by audience
    """
    logger.info("Generating all IRIS memos...")

    # Build narrative at all three levels
    technical_narrative = build_full_narrative(
        model_results, latest, iris_score, features_tail, level="TECHNICAL"
    )
    policy_narrative = build_full_narrative(
        model_results, latest, iris_score, features_tail, level="POLICY"
    )
    plain_narrative = build_full_narrative(
        model_results, latest, iris_score, features_tail, level="PLAIN"
    )

    # Package the shared context
    context = {
        "model_results":      model_results,
        "latest":             latest,
        "iris_score":         iris_score,
        "classification":     classification,
        "signals":            signals,
        "features_tail":      features_tail,
        "generated_at":       datetime.now(),
        "technical_narrative": technical_narrative,
        "policy_narrative":    policy_narrative,
        "plain_narrative":     plain_narrative,
    }

    memos = {}

    # Build each memo
    try:
        memos["governor"] = build_governor_memo(context)
        logger.info("Governor memo built.")
    except Exception as e:
        logger.error(f"Governor memo failed: {e}")
        memos["governor"] = {"error": str(e)}

    try:
        memos["mpc"] = build_mpc_memo(context)
        logger.info("MPC memo built.")
    except Exception as e:
        logger.error(f"MPC memo failed: {e}")
        memos["mpc"] = {"error": str(e)}

    try:
        memos["wananchi"] = build_wananchi_brief(context)
        logger.info("Wananchi brief built.")
    except Exception as e:
        logger.error(f"Wananchi brief failed: {e}")
        memos["wananchi"] = {"error": str(e)}

    logger.info("All memos generated successfully.")
    return memos