# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Risk Gauge Page
# Full-page risk dashboard showing:
#   - The IRIS score gauge prominently
#   - Regime classification with conditions checklist
#   - Component score breakdown
#   - Early warnings in full detail
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go


def render(iris: dict):
    score          = iris["iris_score"]["iris_score"]
    classification = iris["classification"]
    colour         = iris["iris_score"]["regime_colour"]
    regime         = classification["regime"]
    emoji          = classification["regime_emoji"]
    components     = iris["iris_score"]["components"]
    warnings       = classification.get("early_warnings", [])

    st.markdown("## 🎯 Risk Gauge — IRIS Risk Classification")

    # ── Big gauge ──────────────────────────────────────────────────────────────
    col_g, col_r = st.columns([1, 1.5])

    with col_g:
        fig = go.Figure(go.Indicator(
            mode  = "gauge+number",
            value = score,
            title = {"text": f"IRIS Risk Score<br><span style='font-size:0.8em'>{emoji} {regime}</span>",
                     "font": {"size": 16}},
            gauge = {
                "axis": {"range": [0, 100], "tickwidth": 2,
                         "tickvals": [0, 25, 50, 75, 100],
                         "ticktext": ["0", "25", "50", "75", "100"]},
                "bar":  {"color": colour, "thickness": 0.35},
                "steps": [
                    {"range": [0,  25], "color": "#C8E6C9", "name": "Stable"},
                    {"range": [25, 50], "color": "#FFF9C4", "name": "Moderate"},
                    {"range": [50, 75], "color": "#FFE0B2", "name": "Danger"},
                    {"range": [75,100], "color": "#FFCDD2", "name": "Critical"},
                ],
                "threshold": {"line": {"color": colour, "width": 6},
                              "thickness": 0.85, "value": score},
            },
            number={"suffix": "/100", "font": {"size": 42, "color": colour}},
        ))
        fig.update_layout(
            height=340,
            margin=dict(t=30, b=10, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Regime zones legend
        for label, col_hex, rng in [
            ("🟢 STABLE",   "#006400", "0 - 25"),
            ("🟡 MODERATE", "#C5A028", "26 - 50"),
            ("🟠 DANGER",   "#E65100", "51 - 75"),
            ("🔴 CRITICAL", "#8B0000", "76 - 100"),
        ]:
            weight = "bold" if label.split()[1] == regime else "normal"
            bg     = f"{col_hex}22" if label.split()[1] == regime else "transparent"
            st.markdown(f"""
            <div style='background:{bg}; border-left:4px solid {col_hex};
                        padding:0.3rem 0.6rem; margin-bottom:0.3rem;
                        border-radius:4px; font-weight:{weight};'>
                {label} &nbsp;·&nbsp; <span style='color:#777;'>{rng}</span>
            </div>
            """, unsafe_allow_html=True)

    with col_r:
        # Regime description
        st.markdown(f"""
        <div style='background:{colour}18; border:2px solid {colour};
                    border-radius:10px; padding:1.2rem; margin-bottom:1rem;'>
            <div style='font-size:1.3rem; font-weight:bold; color:{colour};'>
                {emoji} {regime} — Score: {score:.1f}/100
            </div>
            <div style='font-size:0.88rem; color:#333; margin-top:0.6rem; line-height:1.6;'>
                {classification.get("description", "")}
            </div>
            <div style='margin-top:0.8rem; padding:0.6rem; background:white;
                        border-radius:6px; font-size:0.85rem; color:#555;'>
                <b>Plain English:</b> {classification.get("plain_english", "")}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Policy signal
        ps_colour = {"LOW": "#006400", "MEDIUM": "#C5A028",
                     "HIGH": "#E65100", "CRITICAL": "#8B0000"}.get(
            classification.get("urgency", "MEDIUM"), "#555")
        st.markdown(f"""
        <div style='background:{ps_colour}18; border-left:5px solid {ps_colour};
                    padding:0.8rem 1rem; border-radius:6px; margin-bottom:1rem;'>
            <div style='font-size:0.75rem; color:{ps_colour}; font-weight:bold;'>
                POLICY SIGNAL · URGENCY: {classification.get("urgency", "N/A")}
            </div>
            <div style='font-size:0.9rem; color:#333; margin-top:0.3rem;'>
                {classification.get("policy_signal", "")}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Conditions checklist
        st.markdown("**Regime Conditions:**")
        for cond in classification.get("conditions", []):
            st.markdown(f"&nbsp;&nbsp;✅ {cond}")

        # Dominant driver
        st.markdown(f"""
        <div style='background:#F5F5F5; border-radius:6px;
                    padding:0.6rem 1rem; margin-top:0.5rem; font-size:0.85rem;'>
            <b>Primary Risk Driver:</b>
            <span style='color:{colour}; font-weight:bold;'>
                {classification.get("dominant_driver", "N/A")}
            </span>
        </div>
        """, unsafe_allow_html=True)

    # ── Component scores ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Component Score Breakdown")

    weights = {
        "inflation_level": 0.20, "real_rate": 0.15,
        "garch_vol": 0.20,       "regime_prob": 0.25,
        "vecm_deviation": 0.10,  "correlation": 0.05,
        "fevd_supply": 0.05,
    }
    labels = {
        "inflation_level": "Inflation Level",
        "real_rate":       "Real Interest Rate",
        "garch_vol":       "GARCH Volatility",
        "regime_prob":     "Regime Probability",
        "vecm_deviation":  "VECM Deviation",
        "correlation":     "Correlation Signal",
        "fevd_supply":     "Supply-Side Risk",
    }
    descriptions = {
        "inflation_level": "Distance of current inflation from CBK's 5% target midpoint",
        "real_rate":       "Nominal interest rate minus inflation — are savers protected?",
        "garch_vol":       "Current inflation volatility relative to historical average",
        "regime_prob":     "Markov model probability of being in the high-inflation regime",
        "vecm_deviation":  "How far the system is from its long-run equilibrium",
        "correlation":     "Fisher Effect stability — are rates moving with inflation?",
        "fevd_supply":     "Structural: how supply-driven is Kenya's inflation?",
    }

    cols = st.columns(len(components))
    for col, (key, val) in zip(cols, components.items()):
        w   = weights.get(key, 0)
        clr = "#8B0000" if val > 75 else "#E65100" if val > 50 else "#C5A028" if val > 25 else "#006400"
        with col:
            st.markdown(f"""
            <div style='text-align:center; background:{clr}18; border:1px solid {clr};
                        border-radius:8px; padding:0.8rem 0.4rem;'>
                <div style='font-size:1.4rem; font-weight:bold; color:{clr};'>{val:.0f}</div>
                <div style='font-size:0.68rem; color:#555; margin-top:0.2rem; line-height:1.3;'>
                    {labels.get(key, key)}
                </div>
                <div style='font-size:0.62rem; color:#999;'>weight: {w*100:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)

    # Descriptions
    st.markdown("")
    with st.expander("What does each component measure?"):
        for key, desc in descriptions.items():
            st.markdown(f"**{labels.get(key, key)}:** {desc}")

    # ── Early warnings ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### Early Warning System — {len(warnings)} Active Warning(s)")

    if not warnings:
        st.success("✅ No active warnings. All indicators are within normal parameters.")
    else:
        sev_styles = {
            "CRITICAL": ("🔴", "#FFEBEE", "#8B0000"),
            "ALERT":    ("🟠", "#FFF3E0", "#E65100"),
            "WARNING":  ("🟡", "#FFFDE7", "#C5A028"),
            "INFO":     ("🔵", "#E3F2FD", "#1565C0"),
        }
        for w in warnings:
            sev = w.get("severity", "INFO")
            icon, bg, col = sev_styles.get(sev, ("⚪", "#F5F5F5", "#555"))
            st.markdown(f"""
            <div style='background:{bg}; border-left:5px solid {col};
                        padding:0.8rem 1rem; border-radius:6px; margin-bottom:0.6rem;'>
                <div style='font-weight:bold; color:{col}; font-size:0.85rem;'>
                    {icon} {sev} · {w["flag"]}
                </div>
                <div style='font-size:0.85rem; color:#333; margin-top:0.4rem; line-height:1.5;'>
                    {w["plain_english"]}
                </div>
            </div>
            """, unsafe_allow_html=True)