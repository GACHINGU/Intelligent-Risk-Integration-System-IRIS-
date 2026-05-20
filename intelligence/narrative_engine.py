# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Narrative Engine
#
# WHAT THIS DOES:
# Takes raw numbers from the model results and converts them into
# clear, human-readable sentences — automatically.
#
# Every number in IRIS tells a story. This engine writes that story.
#
# It produces narrative blocks that are used by:
#   - The memo generator (for formal policy documents)
#   - The Wananchi brief (for plain-English public communication)
#   - The dashboard memorandum page
#
# THREE LANGUAGE LEVELS:
#   TECHNICAL  — for the Governor and MPC (precise, formal)
#   POLICY     — for Treasury and senior officials (clear, actionable)
#   PLAIN      — for the public / wananchi (simple, relatable, Kenyan examples)
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


def _safe(val, fmt=".2f", fallback="N/A"):
    """Safely format a number, returning fallback if None or error."""
    try:
        return format(float(val), fmt)
    except (TypeError, ValueError):
        return fallback


def narrate_current_situation(latest: dict, features_tail: dict,
                               iris_score: dict, level: str = "POLICY") -> str:
    """
    Narrate the current monetary policy situation.

    INPUT:
        latest        — dict with latest inflation and interest_rate readings
        features_tail — dict of most recent feature row
        iris_score    — dict from score_builder
        level         — 'TECHNICAL', 'POLICY', or 'PLAIN'

    OUTPUT: string narrative paragraph
    """
    inf_val   = latest.get("inflation",     {}).get("value")
    ir_val    = latest.get("interest_rate", {}).get("value")
    real_rate = (ir_val - inf_val) if (inf_val and ir_val) else None
    score     = iris_score.get("iris_score",    50)
    regime    = iris_score.get("regime_label", "MODERATE")
    emoji     = iris_score.get("regime_emoji",  "🟡")

    above_target = inf_val is not None and inf_val > 7.5
    negative_rr  = real_rate is not None and real_rate < 0

    if level == "TECHNICAL":
        text = (
            f"Current macroeconomic indicators reflect a {regime} risk environment "
            f"(IRIS composite score: {_safe(score, '.1f')}/100). "
            f"The CPI inflation rate stands at {_safe(inf_val)}%, "
            f"{'exceeding' if above_target else 'within'} the CBK target band of 2.5-7.5%. "
            f"The nominal interest rate is {_safe(ir_val)}%, "
            f"yielding a real interest rate of {_safe(real_rate)}%, "
            f"which is {'negative — indicating ongoing financial repression' if negative_rr else 'positive — consistent with adequate saver protection'}. "
            f"The dominant risk contributor to the composite score is "
            f"{iris_score.get('dominant_driver_label', 'unidentified')}."
        )

    elif level == "POLICY":
        text = (
            f"Kenya's monetary conditions are currently assessed as {emoji} {regime} "
            f"by the IRIS system (score: {_safe(score, '.1f')}/100). "
            f"Inflation at {_safe(inf_val)}% is {'above' if above_target else 'within'} the CBK target. "
            f"The real interest rate of {_safe(real_rate)}% means that "
            f"{'savers are losing purchasing power in real terms' if negative_rr else 'bank deposits are providing positive real returns'}. "
            f"The primary risk driver identified by the model stack is: "
            f"{iris_score.get('dominant_driver_label', 'N/A')}."
        )

    else:  # PLAIN
        inf_str = _safe(inf_val)
        ir_str  = _safe(ir_val)
        rr_str  = _safe(real_rate)
        if above_target:
            target_msg = (
                f"This is above the CBK's target of 7.5%. "
                f"In simple terms: prices are rising faster than the Central Bank wants them to."
            )
        else:
            target_msg = (
                f"This is within the CBK's acceptable range of 2.5-7.5%. "
                f"Prices are rising at a manageable pace."
            )
        if negative_rr:
            rr_msg = (
                f"The real interest rate — what your savings actually earn after inflation — "
                f"is {rr_str}%. This means if you save money in the bank, "
                f"you are actually losing value in real terms. "
                f"Your KES 10,000 today will buy less next year even after earning bank interest."
            )
        else:
            rr_msg = (
                f"The real interest rate is {rr_str}% — positive. "
                f"This means your bank savings are growing faster than prices, "
                f"so your money is holding its value."
            )
        text = (
            f"Right now in Kenya, the inflation rate is {inf_str}% — "
            f"meaning prices are going up by about {inf_str} shillings for every 100 shillings. "
            f"{target_msg} "
            f"The Central Bank's interest rate is {ir_str}%. "
            f"{rr_msg}"
        )

    return text


def narrate_vecm(vecm: dict, level: str = "POLICY") -> str:
    """Narrate VECM findings."""
    if not vecm or vecm.get("error"):
        return "VECM analysis unavailable."

    policy_char = vecm.get("policy_character", "REACTIVE")
    alpha_ir    = vecm.get("alpha_ir",  0)
    alpha_inf   = vecm.get("alpha_inf", 0)
    half_life   = vecm.get("half_life_years")
    beta        = vecm.get("beta_inflation", 0)

    if level == "TECHNICAL":
        return (
            f"The VECM estimates adjustment coefficients of α_IR = {_safe(alpha_ir, '.4f')} "
            f"and α_INF = {_safe(alpha_inf, '.4f')}, indicating that the interest rate "
            f"{'adjusts more rapidly' if abs(alpha_ir) > abs(alpha_inf) else 'adjusts less rapidly'} "
            f"than inflation to restore long-run equilibrium. "
            f"The cointegrating vector implies a long-run beta coefficient of {_safe(beta, '.4f')} "
            f"on inflation. Deviations from equilibrium have a half-life of approximately "
            f"{_safe(half_life, '.1f')} year(s), suggesting "
            f"{'rapid' if half_life and half_life < 2 else 'moderate' if half_life and half_life < 5 else 'slow'} "
            f"mean reversion. Policy character: {policy_char}."
        )

    elif level == "POLICY":
        return (
            f"The VECM confirms that Kenya's monetary policy has been historically {policy_char}. "
            f"{'Interest rates adjust to follow inflation rather than leading it, '  if policy_char == 'REACTIVE' else 'Interest rates tend to move ahead of inflation, '}"
            f"suggesting the CBK {'responds after inflation has already risen' if policy_char == 'REACTIVE' else 'acts pre-emptively'}. "
            f"Deviations from the long-run interest rate-inflation equilibrium "
            f"correct with a half-life of {_safe(half_life, '.1f')} year(s)."
        )

    else:  # PLAIN
        if policy_char == "REACTIVE":
            return (
                "Our model shows that in Kenya's history, the Central Bank has typically "
                "REACTED to rising inflation rather than getting ahead of it. "
                "Think of it like a driver who only brakes AFTER they see the pothole — "
                "not before. This means by the time rates go up, inflation has usually "
                "already caused damage to everyday prices. "
                f"Once things get out of balance, it takes about {_safe(half_life, '.1f')} year(s) "
                f"for the system to correct itself."
            )
        else:
            return (
                "Our model shows the Central Bank has been PROACTIVE — raising rates "
                "before inflation gets out of hand. Like a driver who slows down "
                "when they see a warning sign, not after the crash. "
                f"The system corrects itself within about {_safe(half_life, '.1f')} year(s) "
                f"when it drifts from its normal balance."
            )


def narrate_irf(irf: dict, level: str = "POLICY") -> str:
    """Narrate Impulse Response findings."""
    if not irf or irf.get("error"):
        return "Impulse response analysis unavailable."

    first_neg  = irf.get("first_negative_year")
    peak_yr    = irf.get("peak_year", 0)
    peak_val   = irf.get("peak_value", 0)
    puzzle     = irf.get("price_puzzle", False)
    cum_5      = irf.get("cumulative_5yr",  0)
    cum_10     = irf.get("cumulative_10yr", 0)
    cbk_raises = irf.get("cbk_raises_rates", False)
    cbk_peak   = irf.get("cbk_peak_year", 0)

    if level == "TECHNICAL":
        return (
            f"The orthogonalised IRF shows that a 1 standard deviation shock to the interest rate "
            f"produces {'a positive initial inflation response (price puzzle present)' if puzzle else 'an immediate negative inflation response'}, "
            f"with the first negative inflation effect at period {first_neg if first_neg else 'not detected'}. "
            f"Peak impact of {_safe(peak_val, '.4f')}pp occurs at year {peak_yr}. "
            f"Cumulative 5-year effect: {_safe(cum_5, '.4f')}pp. "
            f"Cumulative 10-year effect: {_safe(cum_10, '.4f')}pp. "
            f"{'The CBK raises rates in response to inflation shocks, peaking at year ' + str(cbk_peak) if cbk_raises else 'No consistent CBK rate response to inflation shocks detected'}."
        )

    elif level == "POLICY":
        lag_msg = (
            f"Rate changes begin reducing inflation around year {first_neg}, "
            f"with peak impact at year {peak_yr}."
            if first_neg else
            "No clear inflation-reducing effect of rate changes is detected in this dataset."
        )
        puzzle_msg = (
            " Note: inflation rises slightly in year 1 before falling (price puzzle) — "
            "businesses temporarily pass on higher borrowing costs before demand slows."
            if puzzle else ""
        )
        return (
            f"The impulse response analysis confirms that the transmission lag for monetary "
            f"policy in Kenya is approximately {first_neg if first_neg else 'unknown'}-{peak_yr} years. "
            f"{lag_msg}{puzzle_msg} "
            f"The MPC must therefore act NOW for effects to materialise in {first_neg if first_neg else 'several'} year(s)."
        )

    else:  # PLAIN
        lag_yrs = first_neg if first_neg else "a few"
        return (
            f"Here is the honest answer to the question every Kenyan deserves: "
            f"'If the CBK raises interest rates today, when will prices actually go down?' "
            f"The answer, based on 53 years of data, is: about {lag_yrs} year(s). "
            f"{'And here is the tricky part: in the first year, prices might actually go up slightly ' if puzzle else ''}"
            f"{'before eventually coming down. This happens because businesses immediately pass ' if puzzle else ''}"
            f"{'on their higher loan costs to you — the customer. ' if puzzle else ''}"
            f"So when you hear the CBK raised rates today, do not expect unga prices "
            f"to drop next week. It takes time. Monetary policy is a slow medicine."
        )


def narrate_fevd(fevd: dict, level: str = "POLICY") -> str:
    """Narrate FEVD findings."""
    if not fevd or fevd.get("error"):
        return "Variance decomposition unavailable."

    ir_share  = fevd.get("ir_share_lr",   14)
    own_share = fevd.get("own_share_lr",  86)
    power     = fevd.get("policy_power", "MODERATE")

    if level == "TECHNICAL":
        return (
            f"The forecast error variance decomposition attributes {ir_share:.1f}% of the "
            f"long-run inflation forecast variance to interest rate shocks, "
            f"with the remaining {own_share:.1f}% attributable to idiosyncratic inflation shocks "
            f"(supply-side: food, fuel, exchange rate). "
            f"This implies {power} monetary policy effectiveness in Kenya. "
            f"At 1-year horizon: {fevd.get('ir_share_1yr', 'N/A')}% IR-explained. "
            f"At 5-year horizon: {fevd.get('ir_share_5yr', 'N/A')}% IR-explained."
        )

    elif level == "POLICY":
        return (
            f"The FEVD reveals that CBK interest rate decisions explain approximately "
            f"{ir_share:.0f}% of Kenya's inflation forecast uncertainty at the long-run horizon. "
            f"The remaining {own_share:.0f}% is driven by supply-side factors — "
            f"food prices, fuel costs, drought, and exchange rate movements — "
            f"that are outside the CBK's direct control. "
            f"This has a critical policy implication: rate hikes alone are insufficient. "
            f"Complementary fiscal and supply-side interventions are essential."
        )

    else:  # PLAIN
        return (
            f"Here is something important that most Kenyans do not know: "
            f"the Central Bank can only directly influence about {ir_share:.0f}% of what drives prices up. "
            f"The other {own_share:.0f}% — things like drought destroying maize crops, "
            f"global fuel prices rising because of wars far away, or the shilling getting weaker — "
            f"those are outside the CBK's hands. "
            f"So when prices rise because it did not rain in the Rift Valley, "
            f"raising interest rates will not make it rain. "
            f"The government needs to invest in irrigation, grain reserves, "
            f"and affordable fuel — not just adjust the CBR."
        )


def narrate_garch(garch: dict, level: str = "POLICY") -> str:
    """Narrate GARCH volatility findings."""
    if not garch or garch.get("error"):
        return "Volatility analysis unavailable."

    current_vol  = garch.get("current_vol",       0)
    hist_avg     = garch.get("historical_avg_vol", 0)
    vol_ratio    = garch.get("vol_ratio",          1)
    persistence  = garch.get("persistence",        0)
    risk         = garch.get("garch_risk",        "MODERATE")
    peak_years   = garch.get("peak_vol_years",    [])

    if level == "TECHNICAL":
        return (
            f"The GARCH(1,1) model with Student-t errors estimates current conditional "
            f"volatility at {_safe(current_vol, '.4f')}pp, relative to a historical "
            f"average of {_safe(hist_avg, '.4f')}pp (ratio: {_safe(vol_ratio, '.2f')}x). "
            f"The volatility persistence parameter (α + β = {_safe(persistence, '.4f')}) "
            f"indicates {'very high' if persistence > 0.95 else 'moderate-high' if persistence > 0.8 else 'moderate'} "
            f"persistence, implying that elevated volatility is "
            f"{'slow to dissipate and requires proactive policy intervention' if persistence > 0.8 else 'expected to self-correct within a reasonable horizon'}. "
            f"Historical peak volatility occurred in years: {peak_years}."
        )

    elif level == "POLICY":
        return (
            f"Inflation volatility is currently {risk} — at {_safe(vol_ratio, '.2f')}x "
            f"the historical average. "
            f"GARCH persistence of {_safe(persistence, '.4f')} means that "
            f"{'once volatility rises, it tends to remain elevated for an extended period without decisive policy action' if persistence > 0.8 else 'volatility is expected to normalise without major intervention'}. "
            f"The MPC should {'act pre-emptively before volatility entrenches' if persistence > 0.8 and vol_ratio > 1.2 else 'continue monitoring volatility trends'}."
        )

    else:  # PLAIN
        if vol_ratio > 1.5:
            mood = (
                f"Right now, inflation is very hard to predict. "
                f"This is the kind of environment where prices can jump significantly "
                f"from one month to the next. For a mama mboga trying to price her tomatoes "
                f"or a landlord deciding next month's rent — this uncertainty is real and costly."
            )
        elif vol_ratio > 1.0:
            mood = (
                f"Right now, inflation is slightly more unpredictable than usual. "
                f"Not at crisis levels, but worth watching carefully. "
                f"For household budgeting — build a small buffer for price surprises."
            )
        else:
            mood = (
                f"Right now, inflation is relatively predictable — below its historical average uncertainty. "
                f"This is a good environment for household budgeting and business planning."
            )
        return mood


def narrate_regime(regime: dict, level: str = "POLICY") -> str:
    """Narrate regime switching findings."""
    if not regime or regime.get("error"):
        return "Regime analysis unavailable."

    current    = regime.get("current_regime",  "LOW_INFLATION")
    p_high     = regime.get("current_p_high",  0)
    p_stay     = regime.get("p_stay_high",     0)
    duration   = regime.get("duration_high_yrs", 0)
    signal     = regime.get("regime_signal",   "STABLE")
    high_years = regime.get("high_inflation_years", [])

    if level == "TECHNICAL":
        return (
            f"The Markov Regime-Switching AR(1) model with switching variance "
            f"identifies two distinct regimes. Current smoothed probability of "
            f"high-inflation regime: P(high) = {p_high:.4f}. "
            f"Regime persistence: P(stay|high) = {p_stay:.4f}, "
            f"implying an expected high-inflation regime duration of {_safe(duration, '.1f')} years. "
            f"Historical high-inflation years: {sorted(high_years)}. "
            f"Current signal: {signal}."
        )

    elif level == "POLICY":
        in_high = p_high > 0.5
        return (
            f"The regime model places Kenya {'in' if in_high else 'outside'} the high-inflation regime "
            f"with {p_high*100:.0f}% probability. "
            f"{'Once in the high-inflation regime, there is a ' + str(round(p_stay*100)) + '% chance of remaining there next year ' if in_high else 'The probability of transitioning to the high-inflation regime next year is ' + str(round(regime.get('p_low_to_high', 0)*100)) + '%. '}"
            f"{'Expected regime duration: ' + _safe(duration, '.1f') + ' years. Decisive policy action is required to exit. ' if in_high else ''}"
            f"Signal: {signal}."
        )

    else:  # PLAIN
        if p_high > 0.7:
            return (
                f"Our model is very confident — {p_high*100:.0f}% sure — that Kenya is currently "
                f"in what we call a 'high-inflation era'. The last time we were deeply in this "
                f"territory was during the 1990s crisis, when unga prices nearly doubled in a single year. "
                f"History tells us that once we enter this era, it tends to last about "
                f"{_safe(duration, '.0f')} years without strong action from the government and CBK. "
                f"This is the time for decisive decisions — not wait-and-see."
            )
        elif p_high > 0.4:
            return (
                f"Our model shows Kenya is at the edge — {p_high*100:.0f}% probability of being "
                f"in a high-inflation era. We are not yet in crisis, but we are walking toward it. "
                f"Think of it like watching storm clouds gather. You do not wait for the rain "
                f"to start before you bring in the clothes."
            )
        else:
            return (
                f"Good news: our model shows Kenya is most likely in a LOW-inflation era "
                f"({(1-p_high)*100:.0f}% confidence). Prices are behaving relatively normally. "
                f"But we monitor this continuously — conditions can change."
            )


def build_full_narrative(model_results: dict, latest: dict,
                          iris_score: dict, features_tail: dict,
                          level: str = "POLICY") -> dict:
    """
    Build the complete narrative package from all model outputs.

    INPUT:
        model_results — dict from model_runner
        latest        — latest indicator readings
        iris_score    — dict from score_builder
        features_tail — most recent feature row as dict
        level         — 'TECHNICAL', 'POLICY', or 'PLAIN'

    OUTPUT: dict with narrative strings for every section
    """
    logger.info(f"Building {level} narrative...")

    narrative = {
        "level":        level,
        "generated_at": datetime.now().isoformat(),

        "situation":    narrate_current_situation(latest, features_tail, iris_score, level),
        "vecm":         narrate_vecm(model_results.get("vecm",   {}), level),
        "irf":          narrate_irf( model_results.get("irf",    {}), level),
        "fevd":         narrate_fevd(model_results.get("fevd",   {}), level),
        "garch":        narrate_garch(model_results.get("garch", {}), level),
        "regime":       narrate_regime(model_results.get("regime", {}), level),

        # Combined summary (used at top of memos)
        "executive_summary": (
            f"{narrate_current_situation(latest, features_tail, iris_score, level)} "
            f"{narrate_regime(model_results.get('regime', {}), level)}"
        ),
    }

    logger.info(f"{level} narrative built successfully.")
    return narrative