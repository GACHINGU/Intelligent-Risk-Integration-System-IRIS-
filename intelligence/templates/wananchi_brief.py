# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Wananchi Brief Template
#
# Plain-English public brief for ordinary Kenyans.
# Language: simple, warm, relatable, with Kenyan examples.
# Tone: like a trusted friend explaining complex things over chai.
# No jargon. No equations. No assumptions of prior knowledge.
#
# This is perhaps the most important document IRIS produces.
# Data only matters when it reaches the people it is meant to serve.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime


def build_wananchi_brief(context: dict) -> dict:
    """Build the Wananchi plain-English brief."""

    iris    = context["iris_score"]
    clf     = context["classification"]
    sigs    = context["signals"]
    models  = context["model_results"]
    latest  = context["latest"]
    nar     = context["plain_narrative"]
    gen_at  = context["generated_at"]

    score   = iris.get("iris_score",    50)
    regime  = iris.get("regime_label", "MODERATE")
    emoji   = iris.get("regime_emoji",  "🟡")
    colour  = iris.get("regime_colour", "#C5A028")

    inf_val  = latest.get("inflation",     {}).get("value")
    ir_val   = latest.get("interest_rate", {}).get("value")
    real_rate = (ir_val - inf_val) if (inf_val and ir_val) else None

    reg     = models.get("regime", {})
    garch   = models.get("garch",  {})
    fevd    = models.get("fevd",   {})

    # Status message in plain English
    if score <= 25:
        status_swahili = "Hali ni shwari."
        status_english = "Things are relatively calm."
        status_advice  = "Your savings in the bank are roughly holding their value. Good time to save."
    elif score <= 50:
        status_swahili = "Angalia kwa makini."
        status_english = "Worth watching closely."
        status_advice  = "Prices are rising a bit faster than ideal. Budget carefully and watch for changes."
    elif score <= 75:
        status_swahili = "Tahadhari — hali inazidi."
        status_english = "Be careful — conditions are becoming strained."
        status_advice  = "Consider diversifying your savings. Prices may continue rising. Plan ahead."
    else:
        status_swahili = "Hali ya dharura — chukua hatua."
        status_english = "Serious situation — take action."
        status_advice  = "Seek advice on protecting your savings. Prices may be volatile. This is not a normal period."

    # What this means for different Kenyans
    if inf_val:
        unga_effect = (
            f"If unga cost KES 100 last year, at {inf_val:.1f}% inflation "
            f"it now costs about KES {100 * (1 + inf_val/100):.0f}. "
            f"That extra KES {100 * inf_val/100:.0f} comes directly from your pocket."
        )
    else:
        unga_effect = "Inflation data currently unavailable."

    if real_rate is not None:
        savings_effect = (
            f"If you saved KES 10,000 in the bank this year earning {ir_val:.1f}% interest, "
            f"by year end you have KES {10000 * (1 + ir_val/100):.0f}. "
            f"But with inflation at {inf_val:.1f}%, that KES {10000 * (1 + ir_val/100):.0f} "
            f"only buys what KES {10000 * (1 + ir_val/100) / (1 + inf_val/100):.0f} bought last year. "
            f"{'You actually lost money in real terms.' if real_rate < 0 else 'You made a small real gain — your money grew faster than prices.'}"
        )
    else:
        savings_effect = "Savings impact data currently unavailable."

    sections = [
        {
            "title": f"📢 WHAT IS HAPPENING RIGHT NOW?",
            "swahili": status_swahili,
            "body": (
                f"{status_english}\n\n"
                f"{nar['situation']}"
            ),
            "advice": status_advice,
        },
        {
            "title": "🌽 WHAT DOES THIS MEAN FOR YOUR UNGA AND DAILY COSTS?",
            "swahili": "Bei za bidhaa zinaathirika vipi?",
            "body": (
                f"{unga_effect}\n\n"
                f"{nar['fevd']}"
            ),
        },
        {
            "title": "💰 WHAT DOES THIS MEAN FOR YOUR SAVINGS?",
            "swahili": "Akiba yako inaathirika vipi?",
            "body": savings_effect,
        },
        {
            "title": "🏦 WHAT IS THE CENTRAL BANK DOING AND IS IT WORKING?",
            "swahili": "Benki Kuu inafanya nini?",
            "body": (
                f"{nar['vecm']}\n\n"
                f"{nar['irf']}"
            ),
        },
        {
            "title": "🌡️ HOW PREDICTABLE ARE PRICES RIGHT NOW?",
            "swahili": "Bei zitakuwa thabiti?",
            "body": nar["garch"],
        },
        {
            "title": "📊 THE BIG PICTURE — WHICH ERA ARE WE IN?",
            "swahili": "Tuko katika kipindi gani cha uchumi?",
            "body": nar["regime"],
        },
        {
            "title": "✅ WHAT CAN YOU DO?",
            "swahili": "Unaweza kufanya nini?",
            "body": (
                "Here is practical advice for every Kenyan based on current conditions:\n\n"
                "• SAVE SMARTLY: Consider Treasury Bills or money market funds rather than "
                "just a savings account. These often earn above inflation.\n\n"
                "• BUDGET FOR CHANGE: Build a 10-15% buffer into your monthly budget "
                "for unexpected price increases — especially on food and fuel.\n\n"
                "• BORROW CAREFULLY: If interest rates are high, expensive loans become "
                "even more burdensome. Only borrow for productive investments.\n\n"
                "• STAY INFORMED: The CBK announces its interest rate decision every two months. "
                "Following this helps you anticipate where borrowing and savings rates are headed.\n\n"
                "• HOLD LEADERS ACCOUNTABLE: Some of Kenya's worst inflation came from "
                "government financial mismanagement. Your vote and your voice matter."
            ),
        },
    ]

    # Plain text full version
    full_text = (
        f"IRIS — WANANCHI BRIEF\n"
        f"{'='*50}\n"
        f"Tarehe / Date: {gen_at.strftime('%d %B %Y')}\n"
        f"Hali ya Sasa / Current Status: {emoji} {regime} — Score {score:.0f}/100\n"
        f"{'='*50}\n\n"
    ) + "\n\n".join([
        f"{'─'*50}\n{s['title']}\n({s.get('swahili','')})\n{'─'*50}\n{s['body']}"
        + (f"\n\n💡 {s['advice']}" if s.get('advice') else '')
        for s in sections
    ])

    return {
        "type":        "WANANCHI_BRIEF",
        "addressee":   "Wananchi wa Kenya — The People of Kenya",
        "from":        "Policy Analysis Unit, Central Bank of Kenya",
        "ref":         f"CBK/PAU/IRIS/{gen_at.strftime('%Y/%m')}/WAN-{gen_at.strftime('%d')}",
        "date":        gen_at.strftime("%d %B %Y"),
        "subject":     f"IRIS Wananchi Brief — {status_swahili} {status_english}",
        "urgency":     clf.get("urgency", "MEDIUM"),
        "regime":      regime,
        "iris_score":  score,
        "colour":      colour,
        "status_swahili": status_swahili,
        "status_english": status_english,
        "status_advice":  status_advice,
        "sections":    sections,
        "full_text":   full_text,
        "generated_at": gen_at.isoformat(),
    }