# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Fisher Effect Live Tracker
#
# WHAT IS THE FISHER EFFECT? (Plain English)
# In theory, when inflation rises by 1%, interest rates should also rise
# by 1% — so that the real return on savings stays constant.
# This is called the Fisher Effect (Irving Fisher, 1930).
#
# In Kenya's data, this relationship has consistently BROKEN DOWN.
# Interest rates have NOT kept pace with inflation, meaning savers
# have repeatedly lost purchasing power.
#
# This page tracks the Fisher Effect in real time.
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy import stats
from dashboard.style.layout import page_header, disclaimer_footer, info_callout


def render(iris: dict):
    features = iris["features"]
    corr     = iris["model_results"].get("correlations", {})
    latest   = iris["latest"]

    inf_val  = latest.get("inflation",     {}).get("value")
    ir_val   = latest.get("interest_rate", {}).get("value")
    real_rate = (ir_val - inf_val) if (inf_val and ir_val) else None

    st.markdown(page_header(
        "📐 Fisher Effect Live Tracker",
        "Are Kenya's interest rates keeping pace with inflation?",
        iris.get("live_available", False),
    ), unsafe_allow_html=True)

    # ── Plain English explanation ──────────────────────────────────────────────
    st.markdown(info_callout(
        "The Fisher Effect predicts that when inflation rises by 1%, "
        "interest rates should also rise by 1% — so savers are protected. "
        "When this breaks down, money quietly loses value in the bank. "
        "This page tracks whether the Fisher Effect is holding in Kenya right now.",
        icon="📖",
    ), unsafe_allow_html=True)

    # ── Current Fisher status ──────────────────────────────────────────────────
    st.markdown("### Current Fisher Effect Status")

    fisher_holds  = corr.get("fisher_holds", False)
    fisher_slope  = corr.get("fisher_slope", 0)
    fisher_r2     = corr.get("fisher_r_squared", 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Fisher Effect",
            "✅ Holding" if fisher_holds else "❌ Broken",
            delta="Rates moving with inflation" if fisher_holds else "Rates lagging inflation",
            delta_color="normal" if fisher_holds else "inverse",
        )
    with col2:
        st.metric(
            "OLS Slope",
            f"{fisher_slope:.3f}",
            delta=f"Target: 1.000 | Gap: {fisher_slope - 1:.3f}",
            delta_color="normal" if abs(fisher_slope - 1) < 0.3 else "inverse",
            help="Fisher Effect predicts slope = 1.0 (rates rise 1-for-1 with inflation)",
        )
    with col3:
        st.metric(
            "Real Interest Rate",
            f"{real_rate:.2f}%" if real_rate is not None else "N/A",
            delta="Savers protected" if real_rate and real_rate > 0 else "Financial repression",
            delta_color="normal" if real_rate and real_rate > 0 else "inverse",
        )
    with col4:
        st.metric(
            "R-squared",
            f"{fisher_r2:.3f}",
            help="How much of interest rate variation is explained by inflation",
        )

    # Status message
    if fisher_holds:
        st.success(corr.get("fisher_plain", ""))
    else:
        st.error(corr.get("fisher_plain", ""))

    # ── Fisher scatter plot with 45° reference ────────────────────────────────
    st.markdown("---")
    st.markdown("### The Fisher Diagram — Interest Rate vs Inflation")
    st.markdown("""
    **How to read this chart:**
    - Each dot = one year
    - **45° dashed line** = perfect Fisher Effect (rates move 1-for-1 with inflation)
    - **Green regression line** = what actually happened in Kenya
    - If green line is below the 45° line → rates did NOT keep pace with inflation
    """)

    years   = features["year"].values
    ir_arr  = features["interest_rate"].values
    inf_arr = features["inflation"].values

    slope, intercept, r_val, p_val, _ = stats.linregress(inf_arr, ir_arr)

    x_line   = np.linspace(inf_arr.min(), inf_arr.max(), 200)
    y_ols    = slope * x_line + intercept
    y_fisher = x_line   # Perfect Fisher: slope=1, intercept=0

    fig = go.Figure()

    # Scatter
    fig.add_trace(go.Scatter(
        x=inf_arr, y=ir_arr,
        mode="markers+text",
        text=[str(int(y)) for y in years],
        textposition="top center",
        textfont=dict(size=7, color="#888"),
        marker=dict(
            color=ir_arr - inf_arr,   # Colour by real rate
            colorscale=[[0, "#8B0000"], [0.5, "#C5A028"], [1, "#006400"]],
            size=9, opacity=0.75,
            colorbar=dict(title="Real Rate (%)", thickness=12),
            line=dict(color="white", width=0.5),
        ),
        name="Annual observations",
        hovertemplate=(
            "<b>Year %{text}</b><br>"
            "Inflation: %{x:.2f}%<br>"
            "Interest Rate: %{y:.2f}%<br>"
            "<extra></extra>"
        ),
    ))

    # Perfect Fisher line (45°)
    fig.add_trace(go.Scatter(
        x=x_line, y=y_fisher,
        mode="lines",
        line=dict(color="#999", width=1.5, dash="dash"),
        name="Perfect Fisher Effect (slope=1.0)",
        hoverinfo="skip",
    ))

    # OLS regression
    fig.add_trace(go.Scatter(
        x=x_line, y=y_ols,
        mode="lines",
        line=dict(color="#006400", width=2.5),
        name=f"Kenya actual (slope={slope:.2f}, R²={r_val**2:.3f})",
        hoverinfo="skip",
    ))

    # Current position
    if inf_val and ir_val:
        fig.add_trace(go.Scatter(
            x=[inf_val], y=[ir_val],
            mode="markers",
            marker=dict(
                color="#1565C0", size=15, symbol="star",
                line=dict(color="white", width=1.5),
            ),
            name=f"Current ({inf_val:.1f}%, {ir_val:.1f}%)",
            hovertemplate=f"<b>Current</b><br>Inflation: {inf_val:.1f}%<br>IR: {ir_val:.1f}%<extra></extra>",
        ))

    fig.add_vline(x=7.5, line_dash="dot", line_color="#006400",
                  annotation_text="CBK target 7.5%", annotation_position="top")
    fig.add_hline(y=0, line_dash="dot", line_color="#999", line_width=0.8)

    fig.update_layout(
        height=480,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,248,0.5)",
        xaxis=dict(title="Inflation Rate (%)", gridcolor="#EEEEEE"),
        yaxis=dict(title="Interest Rate (%)",  gridcolor="#EEEEEE"),
        legend=dict(orientation="h", y=1.05),
        hovermode="closest",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── The Real Rate History ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Real Interest Rate History — Were Savers Protected?")
    st.markdown("""
    **The real interest rate = interest rate minus inflation.**
    When positive → savers earn more than prices rise → money holds its value.
    When negative → inflation outpaces returns → money quietly loses value.
    """)

    real_rate_series = features["real_rate"].values
    rr_years         = features["year"].values

    colours_rr = ["#006400" if v >= 0 else "#8B0000" for v in real_rate_series]

    fig_rr = go.Figure()
    fig_rr.add_trace(go.Bar(
        x=rr_years, y=real_rate_series,
        name="Real Interest Rate",
        marker_color=colours_rr,
        opacity=0.8,
        hovertemplate="<b>%{x}</b>: real rate = %{y:.2f}%<extra></extra>",
    ))
    fig_rr.add_hline(y=0, line_color="black", line_width=1.2)

    # Rolling average
    roll_rr = pd.Series(real_rate_series).rolling(10, min_periods=5).mean()
    fig_rr.add_trace(go.Scatter(
        x=rr_years, y=roll_rr,
        name="10-yr rolling average",
        line=dict(color="#C5A028", width=2.5, dash="dash"),
        hoverinfo="skip",
    ))

    if real_rate is not None:
        fig_rr.add_hline(
            y=real_rate,
            line_color="#1565C0", line_dash="dot", line_width=2,
            annotation_text=f"Current: {real_rate:.2f}%",
            annotation_position="right",
        )

    fig_rr.update_layout(
        height=360,
        margin=dict(t=20, b=20, l=20, r=80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,248,0.5)",
        xaxis=dict(title="Year", gridcolor="#EEEEEE"),
        yaxis=dict(title="Real Interest Rate (%)", gridcolor="#EEEEEE"),
        legend=dict(orientation="h", y=1.05),
        hovermode="x unified",
    )
    st.plotly_chart(fig_rr, use_container_width=True)

    # Summary stats
    n_negative = (real_rate_series < 0).sum()
    n_total    = len(real_rate_series)
    pct_neg    = n_negative / n_total * 100

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("Years with negative real rate", f"{n_negative}/{n_total}")
    with col_s2:
        st.metric("% of time money lost value",    f"{pct_neg:.0f}%")
    with col_s3:
        st.metric("Worst real rate",
                  f"{real_rate_series.min():.2f}%",
                  delta=f"Year {int(features.loc[features['real_rate'].idxmin(), 'year'])}",
                  delta_color="off")
    with col_s4:
        st.metric("Best real rate",
                  f"{real_rate_series.max():.2f}%",
                  delta=f"Year {int(features.loc[features['real_rate'].idxmax(), 'year'])}",
                  delta_color="off")

    st.markdown(f"""
    <div style='background:#FFF3E0; border-left:4px solid #E65100;
                padding:0.8rem 1rem; border-radius:6px; margin-top:1rem;
                font-size:0.88rem; color:#333; line-height:1.6;'>
        <b>Plain English summary:</b><br>
        Kenya's savers had a negative real interest rate in
        <b>{pct_neg:.0f}%</b> of all years studied.
        This means in {pct_neg:.0f} out of every 100 years,
        money kept in the bank lost purchasing power — silently, without most people noticing.
        The Fisher Effect predicts this should not happen.
        That it did — repeatedly — reflects the structural challenges of monetary policy
        in a supply-driven, fiscally-constrained economy.
    </div>
    """, unsafe_allow_html=True)

    st.markdown(disclaimer_footer(), unsafe_allow_html=True)