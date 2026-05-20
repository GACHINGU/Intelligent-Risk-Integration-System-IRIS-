# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Home Page
# The command centre. Shows the IRIS Risk Score prominently,
# key current readings, top signals, and early warnings at a glance.
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime


def render_iris_gauge(score: float, colour: str):
    """Render the big IRIS risk gauge using Plotly."""
    fig = go.Figure(go.Indicator(
        mode  = "gauge+number+delta",
        value = score,
        title = {"text": "IRIS Risk Score", "font": {"size": 18, "color": "#003300"}},
        delta = {"reference": 50, "increasing": {"color": "#8B0000"},
                 "decreasing": {"color": "#006400"}},
        gauge = {
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#003300"},
            "bar":  {"color": colour, "thickness": 0.3},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "#CCCCCC",
            "steps": [
                {"range": [0,  25], "color": "#E8F5E9"},
                {"range": [25, 50], "color": "#FFF9C4"},
                {"range": [50, 75], "color": "#FFE0B2"},
                {"range": [75,100], "color": "#FFCDD2"},
            ],
            "threshold": {
                "line":      {"color": colour, "width": 4},
                "thickness": 0.75,
                "value":     score,
            },
        },
        number = {"suffix": "/100", "font": {"size": 36, "color": colour}},
    ))
    fig.update_layout(
        height=280,
        margin=dict(t=40, b=10, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial"},
    )
    return fig


def render(iris: dict):
    """Render the IRIS Home page."""

    score          = iris["iris_score"]["iris_score"]
    classification = iris["classification"]
    signals        = iris["signals"]
    latest         = iris["latest"]
    features       = iris["features"]
    live_ok        = iris.get("live_available", False)
    loaded_at      = iris.get("loaded_at", datetime.now())

    colour         = iris["iris_score"]["regime_colour"]
    regime         = classification["regime"]
    emoji          = classification["regime_emoji"]

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#003300,#006400);
                padding:1.5rem 2rem; border-radius:10px; margin-bottom:1.5rem;'>
        <h1 style='color:#C5A028; margin:0; font-size:1.8rem;'>
            🇰🇪 IRIS — Intelligent Risk Integration System
        </h1>
        <p style='color:#AAFFAA; margin:0.3rem 0 0 0; font-size:0.9rem;'>
            Kenya Monetary Policy Risk Intelligence · Policy Analysis Unit, CBK ·
            {'🟢 Live Data' if live_ok else '🟡 Historical Data (1971-2023)'} ·
            Updated {loaded_at.strftime('%d %b %Y %H:%M')}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Top row: Gauge + Key Metrics ──────────────────────────────────────────
    col_gauge, col_metrics = st.columns([1, 1.6])

    with col_gauge:
        st.plotly_chart(render_iris_gauge(score, colour), use_container_width=True)
        st.markdown(f"""
        <div style='text-align:center; background:{colour}22; border:2px solid {colour};
                    border-radius:8px; padding:0.6rem; margin-top:-1rem;'>
            <span style='font-size:1.4rem;'>{emoji}</span>
            <span style='font-size:1.1rem; font-weight:bold; color:{colour};'> {regime}</span>
        </div>
        """, unsafe_allow_html=True)

    with col_metrics:
        inf_val = latest.get("inflation",     {}).get("value", "N/A")
        ir_val  = latest.get("interest_rate", {}).get("value", "N/A")
        real_rate = (ir_val - inf_val) if isinstance(ir_val, float) and isinstance(inf_val, float) else None

        st.markdown("#### Current Readings")

        m1, m2 = st.columns(2)
        with m1:
            st.metric(
                label="Inflation Rate",
                value=f"{inf_val:.2f}%" if isinstance(inf_val, float) else "N/A",
                delta=f"{'Above' if isinstance(inf_val, float) and inf_val > 7.5 else 'Within'} CBK target",
                delta_color="inverse",
            )
            st.metric(
                label="GARCH Risk",
                value=iris["model_results"].get("garch", {}).get("garch_risk", "N/A"),
            )
        with m2:
            st.metric(
                label="Interest Rate (CBR)",
                value=f"{ir_val:.2f}%" if isinstance(ir_val, float) else "N/A",
            )
            st.metric(
                label="Real Interest Rate",
                value=f"{real_rate:.2f}%" if real_rate is not None else "N/A",
                delta="Positive — savers protected" if real_rate and real_rate > 0 else "Negative — money losing value",
                delta_color="normal" if real_rate and real_rate > 0 else "inverse",
            )

        st.markdown("---")

        # Regime model reading
        regime_r = iris["model_results"].get("regime", {})
        if regime_r and not regime_r.get("error"):
            p_high = regime_r.get("current_p_high", 0)
            st.markdown(f"""
            <div style='background:#F5F5F5; border-radius:6px; padding:0.6rem 1rem;'>
                <div style='font-size:0.8rem; color:#555; font-weight:bold;'>
                    Markov Regime Model
                </div>
                <div style='margin-top:0.3rem;'>
                    <span style='font-size:1rem; font-weight:bold;
                                 color:{"#8B0000" if p_high > 0.5 else "#006400"};'>
                        {regime_r.get("regime_signal", "N/A")}
                    </span>
                    &nbsp;·&nbsp;
                    <span style='font-size:0.85rem; color:#333;'>
                        P(high-inflation) = {p_high*100:.0f}%
                    </span>
                </div>
                <div style='font-size:0.75rem; color:#777; margin-top:0.2rem;'>
                    Current: {regime_r.get("current_regime", "N/A")}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Component scores bar ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### IRIS Risk Score — Component Breakdown")

    components = iris["iris_score"].get("components", {})
    weights    = {
        "inflation_level": 0.20, "real_rate": 0.15,
        "garch_vol":       0.20, "regime_prob": 0.25,
        "vecm_deviation":  0.10, "correlation": 0.05,
        "fevd_supply":     0.05,
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

    fig_comp = go.Figure()
    comp_names = list(components.keys())
    comp_vals  = [components[k] for k in comp_names]
    comp_labels = [labels.get(k, k) for k in comp_names]
    comp_colours = ["#8B0000" if v > 75 else "#E65100" if v > 50 else
                    "#C5A028" if v > 25 else "#006400" for v in comp_vals]
    weight_labels = [f"(weight: {weights.get(k,0)*100:.0f}%)" for k in comp_names]

    fig_comp.add_trace(go.Bar(
        y=[f"{l}<br><sub>{w}</sub>" for l, w in zip(comp_labels, weight_labels)],
        x=comp_vals,
        orientation="h",
        marker_color=comp_colours,
        text=[f"{v:.1f}" for v in comp_vals],
        textposition="outside",
    ))
    fig_comp.add_vline(x=25, line_dash="dot", line_color="#006400", annotation_text="Stable")
    fig_comp.add_vline(x=50, line_dash="dot", line_color="#C5A028", annotation_text="Moderate")
    fig_comp.add_vline(x=75, line_dash="dot", line_color="#8B0000", annotation_text="Danger")
    fig_comp.update_layout(
        height=300, margin=dict(t=10, b=10, l=10, r=60),
        xaxis=dict(range=[0, 110], title="Score (0-100)"),
        yaxis=dict(title=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # ── Policy signal + Early warnings ────────────────────────────────────────
    col_sig, col_warn = st.columns(2)

    with col_sig:
        st.markdown("#### Policy Signals")
        rate_signal = signals.get("rate_signal", "HOLD")
        sig_colour  = {"HOLD": "#006400", "WATCH AND PREPARE": "#C5A028",
                       "TIGHTEN": "#E65100", "EMERGENCY TIGHTENING": "#8B0000"}.get(rate_signal, "#555")
        st.markdown(f"""
        <div style='background:{sig_colour}22; border-left:5px solid {sig_colour};
                    padding:1rem; border-radius:6px; margin-bottom:0.8rem;'>
            <div style='font-size:0.75rem; color:{sig_colour}; font-weight:bold;'>
                RATE ACTION
            </div>
            <div style='font-size:1.1rem; font-weight:bold; color:{sig_colour};'>
                {rate_signal}
            </div>
        </div>
        """, unsafe_allow_html=True)

        for sig in signals.get("signals", [])[:4]:
            type_colours = {
                "RATE_ACTION":   "#8B0000",
                "RISK_FLAG":     "#E65100",
                "MONITORING":    "#C5A028",
                "COORDINATION":  "#1565C0",
                "COMMUNICATION": "#006400",
            }
            c = type_colours.get(sig["type"], "#555")
            st.markdown(f"""
            <div style='border-left:3px solid {c}; padding:0.4rem 0.8rem;
                        margin-bottom:0.4rem; font-size:0.82rem; color:#333;'>
                <span style='color:{c}; font-weight:bold;'>[{sig["type"]}]</span>
                {sig["action"]}
            </div>
            """, unsafe_allow_html=True)

    with col_warn:
        st.markdown("#### Early Warnings")
        warnings = classification.get("early_warnings", [])
        if not warnings:
            st.success("No active warnings. System is operating within normal parameters.")
        else:
            sev_styles = {
                "CRITICAL": ("🔴", "#FFEBEE", "#8B0000"),
                "ALERT":    ("🟠", "#FFF3E0", "#E65100"),
                "WARNING":  ("🟡", "#FFFDE7", "#C5A028"),
                "INFO":     ("🔵", "#E3F2FD", "#1565C0"),
            }
            for w in warnings[:6]:
                sev = w.get("severity", "INFO")
                icon, bg, col = sev_styles.get(sev, ("⚪", "#F5F5F5", "#555"))
                st.markdown(f"""
                <div style='background:{bg}; border-left:4px solid {col};
                            padding:0.5rem 0.8rem; border-radius:4px; margin-bottom:0.4rem;'>
                    <div style='font-size:0.75rem; font-weight:bold; color:{col};'>
                        {icon} {sev} — {w["flag"]}
                    </div>
                    <div style='font-size:0.78rem; color:#444; margin-top:0.2rem;'>
                        {w["plain_english"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Quick historical context ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Historical Context — Where Are We Now?")

    
    

    fig_ctx = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Interest Rate vs Inflation (1971-2023)",
                        "Real Interest Rate (1971-2023)")
    )

    years = features["year"].values
    ir    = features["interest_rate"].values
    inf_s = features["inflation"].values
    rr    = features["real_rate"].values

    fig_ctx.add_trace(go.Scatter(x=years, y=ir,    name="Interest Rate",
                                  line=dict(color="#006400", width=2)), row=1, col=1)
    fig_ctx.add_trace(go.Scatter(x=years, y=inf_s, name="Inflation",
                                  line=dict(color="#8B0000", width=2, dash="dash")), row=1, col=1)
    fig_ctx.add_hrect(y0=2.5, y1=7.5, fillcolor="#006400", opacity=0.08,
                      annotation_text="CBK Target", row=1, col=1)

    fig_ctx.add_trace(go.Scatter(x=years, y=rr, name="Real Rate",
                                  line=dict(color="#1565C0", width=2),
                                  fill="tozeroy",
                                  fillcolor="rgba(21,101,192,0.1)"), row=1, col=2)
    fig_ctx.add_hline(y=0, line_dash="dot", line_color="#8B0000", row=1, col=2)

    fig_ctx.update_layout(
        height=280,
        margin=dict(t=30, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,248,0.5)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        showlegend=True,
    )
    st.plotly_chart(fig_ctx, use_container_width=True)

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align:center; font-size:0.72rem; color:#AAAAAA;'>
        IRIS v{iris.get('iris_score', {}).get('iris_score', '')} —
        Intelligent Risk Integration System ·
        Policy Analysis Unit, Central Bank of Kenya ·
        Simulated Educational System · Not an official CBK publication
    </div>
    """, unsafe_allow_html=True)