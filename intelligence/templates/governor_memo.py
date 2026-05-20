# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Governor Memo Template
#
# Formal technical memorandum addressed to the CBK Governor.
# Language: precise, institutional, strategic.
# Focus: systemic risk, long-run dynamics, institutional implications.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime


def build_governor_memo(context: dict) -> dict:
    """
    Build the Governor's memorandum.

    INPUT:  context — shared context dict from memo_generator
    OUTPUT: structured memo dict with sections, metadata, and full text
    """
    iris        = context["iris_score"]
    clf         = context["classification"]
    sigs        = context["signals"]
    models      = context["model_results"]
    latest      = context["latest"]
    nar         = context["technical_narrative"]
    gen_at      = context["generated_at"]

    score      = iris.get("iris_score",    50)
    regime     = iris.get("regime_label", "MODERATE")
    emoji      = iris.get("regime_emoji",  "🟡")
    urgency    = clf.get("urgency",        "MEDIUM")
    colour     = iris.get("regime_colour", "#C5A028")

    inf_val    = latest.get("inflation",     {}).get("value")
    ir_val     = latest.get("interest_rate", {}).get("value")
    real_rate  = (ir_val - inf_val) if (inf_val and ir_val) else None

    vecm       = models.get("vecm",   {})
    garch      = models.get("garch",  {})
    coint      = models.get("cointegration", {})
    reg        = models.get("regime", {})

    # Build sections
    sections = [
        {
            "title": "1. IRIS COMPOSITE RISK ASSESSMENT",
            "body": (
                f"The IRIS Intelligent Risk Integration System assigns a composite risk score of "
                f"{score:.1f}/100 to Kenya's current monetary conditions, classifying the "
                f"environment as {emoji} {regime} with urgency level: {urgency}. "
                f"\n\n"
                f"{nar['situation']}"
            ),
        },
        {
            "title": "2. LONG-RUN MONETARY FRAMEWORK INTEGRITY",
            "body": (
                f"Cointegration status: {coint.get('model_choice', 'N/A')} — "
                f"{'the long-run equilibrium relationship between interest rates and inflation is intact' if coint.get('cointegrated') else 'no statistically significant long-run equilibrium detected — monetary anchoring may be compromised'}. "
                f"\n\n{nar['vecm']}"
            ),
        },
        {
            "title": "3. TRANSMISSION MECHANISM ASSESSMENT",
            "body": (
                f"{nar['irf']}"
                f"\n\n{nar['fevd']}"
            ),
        },
        {
            "title": "4. VOLATILITY AND SYSTEMIC RISK",
            "body": (
                f"{nar['garch']}"
                f"\n\n{nar['regime']}"
            ),
        },
        {
            "title": "5. STRATEGIC RECOMMENDATIONS",
            "body": "\n\n".join([
                f"{'R' + str(i+1)}. [{s['type']}] {s['action']}: {s['detail']}"
                for i, s in enumerate(sigs.get("signals", []))
            ]),
        },
        {
            "title": "6. EARLY WARNING FLAGS",
            "body": "\n\n".join([
                f"[{w['severity']}] {w['flag']}: {w['plain_english']}"
                for w in clf.get("early_warnings", [])
            ]) or "No active early warning flags.",
        },
    ]

    # Full plain-text version
    full_text = "\n\n".join([
        f"{'─'*60}\n{s['title']}\n{'─'*60}\n{s['body']}"
        for s in sections
    ])

    return {
        "type":        "GOVERNOR_MEMO",
        "addressee":   "H.E. The Governor, Central Bank of Kenya",
        "from":        "Policy Analysis Unit, IRIS System",
        "ref":         f"CBK/PAU/IRIS/{gen_at.strftime('%Y/%m')}/GOV-{gen_at.strftime('%d')}",
        "date":        gen_at.strftime("%d %B %Y"),
        "subject":     f"IRIS Monetary Risk Assessment — {emoji} {regime} ({score:.1f}/100)",
        "urgency":     urgency,
        "regime":      regime,
        "iris_score":  score,
        "colour":      colour,
        "sections":    sections,
        "full_text":   full_text,
        "generated_at": gen_at.isoformat(),
    }