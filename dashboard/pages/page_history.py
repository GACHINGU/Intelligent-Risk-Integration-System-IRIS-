# ─────────────────────────────────────────────────────────────────────────────
# IRIS — History Page
# Historical context — where are we now vs Kenya's past?
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


def render(iris: dict):
    features = iris["features"]
    latest   = iris["latest"]
    score    = iris["iris_score"]["iris_score"]

    st.markdown("## 📚 Historical Context")
    st.markdown("Where are we now relative to Kenya's 53-year monetary history?")

    inf_val   = latest.get("inflation",     {}).get("value")
    ir_val    = latest.get("interest_rate", {}).get("value")
    real_rate = (ir_val - inf_val) if (inf_val and ir_val) else None

    # ── Era definitions ────────────────────────────────────────────────────────
    eras = [
        (1971, 1990, "#FFF9C4", "#856400", "Financial Repression",
         "Government-controlled low rates. Negative real returns. Silent erosion of savings."),
        (1991, 2003, "#FFCDD2", "#8B0000", "Crisis Era",
         "Goldenberg scandal, hyperinflation (45.98% in 1993), IMF structural adjustment."),
        (2004, 2013, "#C8E6C9", "#006400", "Reform Era",
         "CBK Act 2004, MPC established, inflation targeting, mobile money revolution."),
        (2014, 2023, "#FFF3E0", "#E65100", "Modern Era",
         "COVID-19, Russia-Ukraine war, FX pressure, above-target inflation returns."),
    ]

    # ── Inflation journey ──────────────────────────────────────────────────────
    st.markdown("### Kenya's Inflation Journey — Four Eras")

    fig = go.Figure()
    for start, end, bg_col, line_col, name, desc in eras:
        era_data = features[(features["year"] >= start) & (features["year"] <= end)]
        fig.add_trace(go.Scatter(
            x=era_data["year"], y=era_data["inflation"],
            name=name, line=dict(color=line_col, width=2.5),
            hovertemplate="<b>%{x}</b>: %{y:.2f}%<extra>" + name + "</extra>",
        ))
        fig.add_vrect(x0=start, x1=end, fillcolor=bg_col,
                      opacity=0.3, line_width=0)

    fig.add_hrect(y0=2.5, y1=7.5, fillcolor="#006400", opacity=0.07,
                  annotation_text="CBK target", annotation_position="top right")
    fig.add_hline(y=0, line_dash="dot", line_color="#999", line_width=0.8)

    # Annotate 1993 peak
    fig.add_annotation(x=1993, y=45.98,
                        text="1993: 45.98%<br>Worst crisis",
                        showarrow=True, arrowhead=2,
                        font=dict(color="#8B0000", size=10))

    if inf_val:
        fig.add_hline(y=inf_val, line_dash="dash", line_color="#1565C0",
                      annotation_text=f"Current: {inf_val:.1f}%",
                      annotation_position="right")

    fig.update_layout(
        height=420, margin=dict(t=20, b=20, l=20, r=80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,248,0.5)",
        xaxis=dict(title="Year"),
        yaxis=dict(title="Inflation (%)"),
        legend=dict(orientation="h", y=1.05),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Era cards
    col_eras = st.columns(4)
    for col, (start, end, bg, border, name, desc) in zip(col_eras, eras):
        with col:
            era_data = features[(features["year"] >= start) & (features["year"] <= end)]
            avg_inf  = era_data["inflation"].mean()
            avg_ir   = era_data["interest_rate"].mean()
            avg_rr   = era_data["real_rate"].mean()
            st.markdown(f"""
            <div style='background:{bg}; border:2px solid {border};
                        border-radius:8px; padding:0.8rem; text-align:center;'>
                <div style='font-weight:bold; color:{border}; font-size:0.85rem;'>{name}</div>
                <div style='font-size:0.72rem; color:#555; margin:0.3rem 0;'>{start}-{end}</div>
                <div style='font-size:0.8rem; color:#333;'>Avg inflation: {avg_inf:.1f}%</div>
                <div style='font-size:0.8rem; color:#333;'>Avg IR: {avg_ir:.1f}%</div>
                <div style='font-size:0.8rem; color:{"#8B0000" if avg_rr < 0 else "#006400"};'>
                    Real rate: {avg_rr:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Current position ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Current Position vs Historical Distribution")

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        # Where does current inflation sit in the historical distribution?
        hist_inf = features["inflation"].dropna()
        pct_rank_inf = (hist_inf < inf_val).mean() * 100 if inf_val else None

        fig_hist_inf = go.Figure()
        fig_hist_inf.add_trace(go.Histogram(
            x=hist_inf, nbinsx=20, name="Historical inflation",
            marker_color="#8B0000", opacity=0.6,
        ))
        if inf_val:
            fig_hist_inf.add_vline(x=inf_val, line_color="#1565C0", line_width=3,
                                    annotation_text=f"Current: {inf_val:.1f}%\n(top {100-pct_rank_inf:.0f}%)")
        fig_hist_inf.update_layout(
            height=280, title="Inflation — Where Are We Now?",
            margin=dict(t=40, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Inflation (%)"),
            yaxis=dict(title="Count"),
        )
        st.plotly_chart(fig_hist_inf, use_container_width=True)
        if pct_rank_inf:
            st.caption(f"Current inflation ({inf_val:.1f}%) is higher than {pct_rank_inf:.0f}% of all historical years.")

    with col_h2:
        hist_rr = features["real_rate"].dropna()
        pct_rank_rr = (hist_rr < real_rate).mean() * 100 if real_rate is not None else None

        fig_hist_rr = go.Figure()
        fig_hist_rr.add_trace(go.Histogram(
            x=hist_rr, nbinsx=20, name="Historical real rate",
            marker_color="#1565C0", opacity=0.6,
        ))
        if real_rate is not None:
            fig_hist_rr.add_vline(x=real_rate, line_color="#8B0000", line_width=3,
                                   annotation_text=f"Current: {real_rate:.1f}%")
        fig_hist_rr.add_vline(x=0, line_dash="dot", line_color="#333")
        fig_hist_rr.update_layout(
            height=280, title="Real Rate — Where Are We Now?",
            margin=dict(t=40, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Real Interest Rate (%)"),
            yaxis=dict(title="Count"),
        )
        st.plotly_chart(fig_hist_rr, use_container_width=True)
        if pct_rank_rr is not None:
            st.caption(f"Current real rate ({real_rate:.1f}%) is {'below' if real_rate < 0 else 'above'} zero — "
                       f"{'money is losing value' if real_rate < 0 else 'savers are being protected'}.")

    # ── Most similar historical year ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Most Comparable Historical Years")
    st.markdown("Which past years most closely resemble current conditions?")

    if inf_val and ir_val:
        features_copy = features.copy()
        features_copy["distance"] = np.sqrt(
            (features_copy["inflation"]     - inf_val) ** 2 +
            (features_copy["interest_rate"] - ir_val)  ** 2
        )
        closest = features_copy.nsmallest(5, "distance")[
            ["year", "inflation", "interest_rate", "real_rate", "distance"]
        ].round(3)
        closest.columns = ["Year", "Inflation %", "Interest Rate %", "Real Rate %", "Similarity Distance"]
        st.dataframe(closest, use_container_width=True, hide_index=True)
        closest_yr = int(closest.iloc[0]["Year"])
        st.info(f"Current conditions most closely resemble Kenya in **{closest_yr}** — "
                f"review that period's context for analogous policy lessons.")