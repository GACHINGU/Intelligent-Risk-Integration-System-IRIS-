# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Impulse Response Functions (IRF)
#
# WHAT IS AN IRF? (Plain English)
# Imagine dropping a stone into a still pond.
# The stone = a sudden shock (e.g. CBK raises rates by 1%)
# The ripples = how the rest of the economy responds over time
# The IRF traces those ripples — year by year — for up to 10 years.
#
# KEY QUESTIONS THE IRF ANSWERS FOR IRIS:
#   1. If CBK raises rates by 1% TODAY, what happens to inflation
#      over the next 1, 2, 3... 10 years?
#   2. If inflation suddenly spikes by 1%, how does the CBK respond
#      over the same horizon?
#
# KEY SIGNALS FROM THE IRF:
#   - Does inflation fall after a rate hike? (Good — policy works)
#   - How many years before it falls? (The transmission lag)
#   - Does inflation RISE first before falling? (The price puzzle)
#   - Does the CBK raise rates when inflation spikes? (Reactive/proactive)
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)


def run_irf(vecm_result: dict, periods: int = 10) -> dict:
    """
    Compute Impulse Response Functions from a fitted VECM.

    INPUT:
        vecm_result — dict returned by models.vecm.run_vecm()
        periods     — how many years ahead to compute (default 10)

    OUTPUT: dict with IRF arrays and plain-English interpretations
    """
    fitted = vecm_result.get("fitted")

    if fitted is None:
        logger.error("IRF: No fitted VECM provided.")
        return {"error": "No fitted VECM model available"}

    try:
        # ── Compute IRF ───────────────────────────────────────────────────────
        irf_obj = fitted.irf(periods=periods)

        # irf_obj.irfs shape: (periods+1, n_vars, n_vars)
        # Variable order: 0 = interest_rate, 1 = inflation
        # irf_obj.irfs[t, response, impulse]

        # ── Extract the four key response paths ───────────────────────────────
        # 1. IR shock → Inflation response (KEY POLICY QUESTION)
        ir_to_inf  = irf_obj.irfs[:, 1, 0].tolist()

        # 2. Inflation shock → IR response (Is CBK reactive?)
        inf_to_ir  = irf_obj.irfs[:, 0, 1].tolist()

        # 3. IR shock → IR own response (persistence of rate shocks)
        ir_to_ir   = irf_obj.irfs[:, 0, 0].tolist()

        # 4. Inflation shock → Inflation own response (inflation persistence)
        inf_to_inf = irf_obj.irfs[:, 1, 1].tolist()

        # ── Analyse the IR → Inflation path ───────────────────────────────────
        ir_to_inf_arr = np.array(ir_to_inf)

        # Find when inflation first turns negative (i.e. rate hike starts working)
        neg_periods = np.where(ir_to_inf_arr < 0)[0]
        first_negative_year = int(neg_periods[0]) if len(neg_periods) > 0 else None

        # Find peak impact year (largest absolute response)
        peak_year   = int(np.argmax(np.abs(ir_to_inf_arr)))
        peak_value  = round(float(ir_to_inf_arr[peak_year]), 4)

        # Price puzzle: does inflation RISE in year 1 after a rate hike?
        price_puzzle = ir_to_inf_arr[1] > 0 if len(ir_to_inf_arr) > 1 else False

        # Cumulative effect at 5 and 10 years
        cum_5yr  = round(float(np.sum(ir_to_inf_arr[:min(6,  len(ir_to_inf_arr))])), 4)
        cum_10yr = round(float(np.sum(ir_to_inf_arr[:min(11, len(ir_to_inf_arr))])), 4)

        # ── Analyse the Inflation → IR path ───────────────────────────────────
        inf_to_ir_arr  = np.array(inf_to_ir)
        cbk_peak_year  = int(np.argmax(np.abs(inf_to_ir_arr)))
        cbk_peak_value = round(float(inf_to_ir_arr[cbk_peak_year]), 4)

        # Does CBK raise rates when inflation rises? (positive response)
        cbk_raises_rates = inf_to_ir_arr[1] > 0 if len(inf_to_ir_arr) > 1 else False

        # ── Plain English interpretations ─────────────────────────────────────
        if first_negative_year is not None:
            transmission_plain = (
                f"A 1% CBK rate hike begins reducing inflation around year {first_negative_year}. "
                f"The peak impact occurs at year {peak_year} ({peak_value:+.2f}%). "
                f"The full transmission lag is approximately {first_negative_year}-{peak_year} years."
            )
        else:
            transmission_plain = (
                "The model does not show a clear negative inflation response to a rate hike. "
                "This suggests weak monetary policy transmission in Kenya's economy."
            )

        price_puzzle_plain = (
            "The PRICE PUZZLE is present: inflation RISES slightly in year 1 after a rate hike "
            "before eventually falling. This is common in developing economies — businesses "
            "immediately pass on higher borrowing costs to consumers, even as demand slows."
            if price_puzzle else
            "No price puzzle detected — inflation begins responding to rate hikes immediately."
        )

        cbk_response_plain = (
            f"When inflation rises by 1%, the CBK raises interest rates — "
            f"peaking at year {cbk_peak_year} ({cbk_peak_value:+.2f}%). "
            f"This is REACTIVE monetary policy — the CBK responds AFTER inflation has risen."
            if cbk_raises_rates else
            "The model suggests the CBK does not consistently raise rates when inflation rises. "
            "This is a significant monetary policy concern."
        )

        result = {
            "periods":            periods,

            # Raw IRF arrays (for plotting)
            "ir_to_inf":          ir_to_inf,
            "inf_to_ir":          inf_to_ir,
            "ir_to_ir":           ir_to_ir,
            "inf_to_inf":         inf_to_inf,

            # Key metrics — IR to inflation
            "first_negative_year":  first_negative_year,
            "peak_year":            peak_year,
            "peak_value":           peak_value,
            "price_puzzle":         price_puzzle,
            "cumulative_5yr":       cum_5yr,
            "cumulative_10yr":      cum_10yr,

            # Key metrics — inflation to IR
            "cbk_peak_year":        cbk_peak_year,
            "cbk_peak_value":       cbk_peak_value,
            "cbk_raises_rates":     cbk_raises_rates,

            # Plain English
            "transmission_plain":   transmission_plain,
            "price_puzzle_plain":   price_puzzle_plain,
            "cbk_response_plain":   cbk_response_plain,
        }

        logger.info(f"IRF computed. First negative inflation response: year {first_negative_year}. "
                    f"Price puzzle: {price_puzzle}. CBK raises rates: {cbk_raises_rates}.")

        return result

    except Exception as e:
        logger.error(f"IRF computation failed: {e}")
        return {"error": str(e)}