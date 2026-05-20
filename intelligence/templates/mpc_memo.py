# ─────────────────────────────────────────────────────────────────────────────
# IRIS — MPC Memo Template
#
# Operational memorandum for the Monetary Policy Committee.
# Language: clear, actionable, recommendation-driven.
# Focus: what to do at the next MPC meeting and why.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime


def build_mpc_memo(context: dict) -> dict:
    """Build the MPC operational memorandum."""

    iris    = context["iris_score"]
    clf     = context["classification"]
    sigs    = context["signals"]
    models  = context["model_results"]
    latest  = context["latest"]
    nar     = context["policy_narrative"]
    gen_at  = context["generated_at"]

    score   = iris.get("iris_score",    50)
    regime  = iris.get("regime_label", "MODERATE")
    emoji   = iris.get("regime_emoji",  "🟡")
    colour  = iris.get("regime_colour", "#C5A028")
    urgency = clf.get("urgency",        "MEDIUM")

    inf_val  = latest.get("inflation",     {}).get("value")
    ir_val   = latest.get("interest_rate", {}).get("value")
    real_rate = (ir_val - inf_val) if (inf_val and ir_val) else None

    irf     = models.get("irf",     {})
    fevd    = models.get("fevd",    {})
    reg     = models.get("regime",  {})
    garch   = models.get("garch",   {})

    # Rate signal
    rate_signal = sigs.get("rate_signal", "HOLD")
    rate_colour = {
        "HOLD":                 "#006400",
        "WATCH AND PREPARE":    "#C5A028",
        "TIGHTEN":              "#E65100",
        "EMERGENCY TIGHTENING": "#8B0000",
    }.get(rate_signal, "#555555")

    sections = [
        {
            "title": "1. SITUATION SUMMARY",
            "body": nar["situation"],
        },
        {
            "title": "2. RECOMMENDED RATE ACTION",
            "body": (
                f"IRIS RATE SIGNAL: {rate_signal}\n\n"
                f"{next((s['detail'] for s in sigs.get('signals', []) if s['type'] == 'RATE_ACTION'), 'No rate action signal generated.')}"
            ),
            "highlight": True,
            "highlight_colour": rate_colour,
        },
        {
            "title": "3. TRANSMISSION LAG CONTEXT",
            "body": (
                f"{nar['irf']}\n\n"
                f"Implication for meeting timing: rate decisions made at this meeting will "
                f"have their primary effect approximately "
                f"{irf.get('first_negative_year', 'N/A')}-{irf.get('peak_year', 'N/A')} "
                f"year(s) from now. Forward guidance should reflect this lag explicitly."
            ),
        },
        {
            "title": "4. SUPPLY-SIDE CONSTRAINT",
            "body": (
                f"{nar['fevd']}\n\n"
                f"Recommendation: The Committee's post-meeting statement should explicitly "
                f"acknowledge the {fevd.get('own_share_lr', 86):.0f}% supply-driven component "
                f"of inflation and outline the complementary fiscal measures being coordinated "
                f"with National Treasury."
            ),
        },
        {
            "title": "5. VOLATILITY AND REGIME RISK",
            "body": (
                f"{nar['garch']}\n\n"
                f"{nar['regime']}\n\n"
                f"Regime signal: {reg.get('regime_signal', 'N/A')} — "
                f"P(high-inflation regime) = {reg.get('current_p_high', 0)*100:.0f}%."
            ),
        },
        {
            "title": "6. FULL SIGNAL SET",
            "body": "\n\n".join([
                f"[Priority {i+1}] [{s['type']}] {s['action']}\n{s['detail']}"
                for i, s in enumerate(sigs.get("signals", []))
            ]),
        },
        {
            "title": "7. ACTIVE WARNINGS",
            "body": "\n".join([
                f"• [{w['severity']}] {w['flag']}: {w['plain_english']}"
                for w in clf.get("early_warnings", [])
            ]) or "No active warnings.",
        },
        {
            "title": "8. COMMUNICATION GUIDANCE",
            "body": (
                "The following points are recommended for the post-MPC press statement:\n\n"
                + "\n".join([
                    f"• {s['detail']}"
                    for s in sigs.get("signals", [])
                    if s["type"] == "COMMUNICATION"
                ])
                or "No specific communication guidance generated."
            ),
        },
    ]

    full_text = "\n\n".join([
        f"{'─'*60}\n{s['title']}\n{'─'*60}\n{s['body']}"
        for s in sections
    ])

    return {
        "type":        "MPC_MEMO",
        "addressee":   "The Chairperson & Members, Monetary Policy Committee",
        "from":        "Policy Analysis Unit, IRIS System",
        "ref":         f"CBK/MPC/IRIS/{gen_at.strftime('%Y/%m')}/MPC-{gen_at.strftime('%d')}",
        "date":        gen_at.strftime("%d %B %Y"),
        "subject":     f"IRIS MPC Pre-Meeting Brief — Rate Signal: {rate_signal}",
        "urgency":     urgency,
        "regime":      regime,
        "iris_score":  score,
        "rate_signal": rate_signal,
        "rate_colour": rate_colour,
        "colour":      colour,
        "sections":    sections,
        "full_text":   full_text,
        "generated_at": gen_at.isoformat(),
    }