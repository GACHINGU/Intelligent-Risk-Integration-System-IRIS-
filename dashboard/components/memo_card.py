# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Memo Card Component
# Renders a single memo section as a styled card.
# Used by page_memorandum.py for consistent section rendering.
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
from dashboard.style.theme import COLOURS, RISK_META, SEVERITY_META


def memo_header(memo: dict):
    """Render the memo letterhead and metadata."""
    colour  = memo.get("colour", COLOURS["cbk_green"])
    score   = memo.get("iris_score", 50)
    regime  = memo.get("regime", "MODERATE")
    urgency = memo.get("urgency", "MEDIUM")
    date    = memo.get("date", "")
    ref     = memo.get("ref",  "")

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#003300,#006400);
                padding:1.2rem 1.8rem; border-radius:10px; margin-bottom:1.2rem;'>
        <div style='font-size:0.75rem; color:#C5A028; font-weight:bold;
                    letter-spacing:2px; margin-bottom:0.4rem;'>
            CENTRAL BANK OF KENYA — IRIS POLICY ANALYSIS UNIT
        </div>
        <div style='font-size:1.4rem; font-weight:bold; color:white;'>
            {memo.get("type","MEMO").replace("_"," ")}
        </div>
        <div style='font-size:0.85rem; color:#AAFFAA; margin-top:0.3rem;'>
            {memo.get("subject","")}
        </div>
        <div style='display:flex; gap:2rem; margin-top:0.8rem;
                    font-size:0.78rem; color:#CCCCCC;'>
            <span><b>TO:</b> {memo.get("addressee","")}</span>
            <span><b>DATE:</b> {date}</span>
            <span><b>REF:</b> {ref}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # IRIS score summary row
    meta = RISK_META.get(regime, RISK_META["MODERATE"])
    st.markdown(f"""
    <div style='background:{meta["bg"]}; border:2px solid {meta["colour"]};
                border-radius:8px; padding:0.8rem 1.2rem; margin-bottom:1rem;
                display:flex; justify-content:space-between; align-items:center;'>
        <div>
            <span style='font-size:1.5rem;'>{meta["emoji"]}</span>
            <span style='font-size:1.1rem; font-weight:bold; color:{meta["colour"]};
                         margin-left:0.4rem;'>
                {regime} — IRIS Score: {score:.1f}/100
            </span>
        </div>
        <div style='font-size:0.82rem; color:#555;'>
            Urgency: <b style='color:{meta["colour"]};'>{urgency}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)


def memo_section(section: dict, colour: str = "#006400"):
    """Render one memo section with its heading and body."""
    title    = section.get("title", "")
    body     = section.get("body",  "")
    swahili  = section.get("swahili", "")
    advice   = section.get("advice",  "")
    highlight = section.get("highlight", False)
    hl_colour = section.get("highlight_colour", colour)

    # Section heading
    swahili_bit = f" &nbsp;·&nbsp; <i style='font-size:0.82rem;'>{swahili}</i>" if swahili else ""
    st.markdown(f"""
    <div style='background:{colour}; color:white; font-weight:bold;
                padding:0.5rem 1rem; border-radius:4px;
                margin:1rem 0 0.5rem 0; font-size:0.9rem;'>
        {title}{swahili_bit}
    </div>
    """, unsafe_allow_html=True)

    # Highlighted action box (for rate signal)
    if highlight:
        st.markdown(f"""
        <div style='background:{hl_colour}20; border-left:5px solid {hl_colour};
                    padding:0.8rem 1rem; border-radius:6px; margin-bottom:0.6rem;
                    font-size:0.9rem; font-weight:bold; color:{hl_colour};'>
            {body[:300]}
        </div>
        """, unsafe_allow_html=True)
        return

    # Normal body — render paragraph by paragraph
    for para in body.split("\n\n"):
        para = para.strip()
        if para:
            if para.startswith("•"):
                st.markdown(para)
            else:
                st.markdown(f"""
                <div style='font-size:0.88rem; color:#333; line-height:1.6;
                            margin-bottom:0.4rem;'>{para}</div>
                """, unsafe_allow_html=True)

    # Advice callout
    if advice:
        st.info(f"💡 {advice}")


def warning_card(warning: dict):
    """Render a single early warning card."""
    sev  = warning.get("severity", "WARNING")
    meta = SEVERITY_META.get(sev, SEVERITY_META["WARNING"])

    st.markdown(f"""
    <div style='background:{meta["bg"]}; border-left:5px solid {meta["colour"]};
                padding:0.7rem 1rem; border-radius:6px; margin-bottom:0.5rem;'>
        <div style='font-weight:bold; color:{meta["colour"]}; font-size:0.82rem;'>
            {meta["icon"]} {sev} — {warning.get("flag","")}
        </div>
        <div style='font-size:0.82rem; color:#333; margin-top:0.3rem; line-height:1.5;'>
            {warning.get("plain_english","")}
        </div>
    </div>
    """, unsafe_allow_html=True)


def signal_card(signal: dict):
    """Render a single policy signal card."""
    type_colours = {
        "RATE_ACTION":   "#8B0000",
        "RISK_FLAG":     "#E65100",
        "MONITORING":    "#C5A028",
        "COORDINATION":  "#1565C0",
        "COMMUNICATION": "#006400",
    }
    colour = type_colours.get(signal.get("type", ""), "#555")

    st.markdown(f"""
    <div style='border-left:4px solid {colour}; padding:0.6rem 1rem;
                margin-bottom:0.5rem; background:{colour}10; border-radius:4px;'>
        <div style='font-size:0.78rem; color:{colour}; font-weight:bold;'>
            [{signal.get("type","")}] Priority {signal.get("priority","")}
        </div>
        <div style='font-size:0.88rem; font-weight:bold; color:#222; margin:0.2rem 0;'>
            {signal.get("action","")}
        </div>
        <div style='font-size:0.82rem; color:#444; line-height:1.5;'>
            {signal.get("detail","")}
        </div>
    </div>
    """, unsafe_allow_html=True)