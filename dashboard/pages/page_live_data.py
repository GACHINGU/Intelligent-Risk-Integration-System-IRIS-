# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Live Data Page
# Shows the most recent data readings, trend sparklines,
# and the full historical series in interactive charts.
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def render(iris: dict):
    features   = iris["features"]
    latest     = iris["latest"]
    live_ok    = iris.get("live_available", False)
    loaded_at  = iris.get("loaded_at")

    st.markdown("## 📡 Live Data Feed")
    st.markdown(f"""
    <div style='background:#E8F5E9; border-left:4px solid #006400;
                padding:0.8rem 1rem; border-radius:6px; margin-bottom:1rem;'>
        {'🟢 <b>Live data active</b> — pulling from Trading Economics API' if live_ok
         else '🟡 <b>Historical data mode</b> — no API key detected. Showing 1971-2023 historical baseline.'}
        {'&nbsp;·&nbsp;Last updated: ' + loaded_at.strftime('%d %b %Y at %H:%M') if loaded_at else ''}
    </div>
    """, unsafe_allow_html=True)

    # ── Latest readings ────────────────────────────────────────────────────────
    st.markdown("### Latest Readings")
    inf_val = latest.get("inflation",     {}).get("value")
    ir_val  = latest.get("interest_rate", {}).get("value")
    inf_date = latest.get("inflation",     {}).get("date", "")
    ir_date  = latest.get("interest_rate", {}).get("date", "")

    real_rate = (ir_val - inf_val) if (inf_val is not None and ir_val is not None) else None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("CPI Inflation",    f"{inf_val:.2f}%" if inf_val else "N/A",
                  delta=f"As of {inf_date}" if inf_date else "")
    with col2:
        st.metric("CBK Interest Rate", f"{ir_val:.2f}%" if ir_val else "N/A",
                  delta=f"As of {ir_date}" if ir_date else "")
    with col3:
        st.metric("Real Interest Rate", f"{real_rate:.2f}%" if real_rate is not None else "N/A",
                  delta="Savers protected" if real_rate and real_rate > 0 else "Money losing value",
                  delta_color="normal" if real_rate and real_rate > 0 else "inverse")
    with col4:
        above = inf_val is not None and inf_val > 7.5
        st.metric("vs CBK Target",
                  "Above target" if above else "In target",
                  delta=f"{inf_val - 7.5:.2f}pp above" if above and inf_val else "Within 2.5-7.5% band",
                  delta_color="inverse" if above else "normal")

    # ── Interactive time series ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Historical Series")

    years  = features["year"].values
    ir_arr = features["interest_rate"].values
    inf_arr = features["inflation"].values
    rr_arr  = features["real_rate"].values

    view = st.radio("View",
                    ["Both Series", "Interest Rate only", "Inflation only", "Real Rate"],
                    horizontal=True)

    fig = go.Figure()

    if view in ["Both Series", "Interest Rate only"]:
        fig.add_trace(go.Scatter(
            x=years, y=ir_arr, name="Interest Rate",
            line=dict(color="#006400", width=2.5),
            hovertemplate="<b>Year:</b> %{x}<br><b>Interest Rate:</b> %{y:.2f}%<extra></extra>",
        ))

    if view in ["Both Series", "Inflation only"]:
        fig.add_trace(go.Scatter(
            x=years, y=inf_arr, name="Inflation",
            line=dict(color="#8B0000", width=2.5, dash="dash"),
            hovertemplate="<b>Year:</b> %{x}<br><b>Inflation:</b> %{y:.2f}%<extra></extra>",
        ))

    if view == "Real Rate":
        fig.add_trace(go.Scatter(
            x=years, y=rr_arr, name="Real Interest Rate",
            line=dict(color="#1565C0", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(21,101,192,0.1)",
            hovertemplate="<b>Year:</b> %{x}<br><b>Real Rate:</b> %{y:.2f}%<extra></extra>",
        ))

    # CBK target band
    if view != "Real Rate":
        fig.add_hrect(y0=2.5, y1=7.5, fillcolor="#006400", opacity=0.07,
                      annotation_text="CBK target band (2.5-7.5%)",
                      annotation_position="top right")

    fig.add_hline(y=0, line_dash="dot", line_color="#999", line_width=0.8)

    fig.update_layout(
        height=420,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,248,0.5)",
        xaxis=dict(title="Year", gridcolor="#EEEEEE"),
        yaxis=dict(title="Rate (%)", gridcolor="#EEEEEE"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Decade summary table ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Decade-by-Decade Summary")

    df = features.copy()
    df["decade"] = (df["year"] // 10) * 10
    decade_summary = df.groupby("decade").agg(
        Avg_Inflation   = ("inflation",     "mean"),
        Avg_IR          = ("interest_rate", "mean"),
        Avg_Real_Rate   = ("real_rate",     "mean"),
        Max_Inflation   = ("inflation",     "max"),
        Min_Real_Rate   = ("real_rate",     "min"),
        Years_Above_Target = ("above_target", "sum"),
    ).round(2).reset_index()
    decade_summary.columns = [
        "Decade", "Avg Inflation %", "Avg Interest Rate %", "Avg Real Rate %",
        "Peak Inflation %", "Min Real Rate %", "Years Above 7.5% Target"
    ]
    decade_summary["Decade"] = decade_summary["Decade"].astype(str) + "s"

    def colour_real_rate(val):
        if isinstance(val, float):
            color = "#FFCDD2" if val < 0 else "#C8E6C9"
            return f"background-color: {color}"
        return ""

    styled = (
        decade_summary.style
        .applymap(colour_real_rate, subset=["Avg Real Rate %", "Min Real Rate %"])
        .format("{:.2f}", subset=["Avg Inflation %", "Avg Interest Rate %",
                                   "Avg Real Rate %", "Peak Inflation %", "Min Real Rate %"])
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.caption("🟢 Green = positive real rate (savers protected)  |  🔴 Red = negative real rate (money losing value)")