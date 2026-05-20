# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Correlations Page
# Static, dynamic, cross-correlation, lead-lag, and Fisher Effect.
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def render(iris: dict):
    corr     = iris["model_results"].get("correlations", {})
    features = iris["features"]

    st.markdown("## 📊 Correlation Analysis")

    if corr.get("error"):
        st.error(f"Correlation analysis error: {corr['error']}")
        return

    # ── Static correlations ────────────────────────────────────────────────────
    st.markdown("### Static Correlations — Full Sample (1971-2023)")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Pearson r",   f"{corr.get('pearson_r',  'N/A'):.4f}",
                        delta="Significant" if corr.get("pearson_p", 1) < 0.05 else "Not significant")
    with c2: st.metric("Pearson p",   f"{corr.get('pearson_p',  'N/A'):.4f}")
    with c3: st.metric("Spearman ρ",  f"{corr.get('spearman_r', 'N/A'):.4f}",
                        delta="Significant" if corr.get("spearman_p", 1) < 0.05 else "Not significant")
    with c4: st.metric("Spearman p",  f"{corr.get('spearman_p', 'N/A'):.4f}")

    st.info(corr.get("pearson_plain", ""))

    # ── Scatter with OLS ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Scatter Plot — Interest Rate vs Inflation")

    from scipy import stats as scipy_stats
    years   = features["year"].values
    ir_arr  = features["interest_rate"].values
    inf_arr = features["inflation"].values

    slope, intercept, r_val, p_val, _ = scipy_stats.linregress(inf_arr, ir_arr)
    x_line = [float(min(inf_arr)), float(max(inf_arr))]
    y_line = [slope * x + intercept for x in x_line]

    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(
        x=inf_arr, y=ir_arr, mode="markers+text",
        text=[str(int(y)) for y in years],
        textposition="top center",
        textfont=dict(size=7, color="#888"),
        marker=dict(color="#006400", size=8, opacity=0.7,
                    line=dict(color="white", width=0.5)),
        name="Annual observations",
        hovertemplate="<b>Year:</b> %{text}<br><b>Inflation:</b> %{x:.2f}%<br><b>IR:</b> %{y:.2f}%<extra></extra>",
    ))
    fig_scatter.add_trace(go.Scatter(
        x=x_line, y=y_line, mode="lines",
        line=dict(color="#8B0000", width=2, dash="dash"),
        name=f"OLS (R²={r_val**2:.3f})",
    ))
    fig_scatter.add_vline(x=7.5, line_dash="dot", line_color="#006400",
                           annotation_text="CBK upper target")
    fig_scatter.update_layout(
        height=400, margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,248,0.5)",
        xaxis=dict(title="Inflation Rate (%)"),
        yaxis=dict(title="Interest Rate (%)"),
        legend=dict(orientation="h", y=1.02),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # ── Rolling correlation ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Rolling 10-Year Correlation — Has the Relationship Changed Over Time?")
    st.info(corr.get("rolling_plain", ""))

    roll_corr  = corr.get("roll_corr", [])
    roll_years = corr.get("roll_corr_years", [])
    sig_thr    = corr.get("sig_threshold", 0.27)

    if roll_corr and roll_years:
        roll_vals = [v for v in roll_corr]
        fig_roll = go.Figure()
        fig_roll.add_trace(go.Scatter(
            x=roll_years, y=roll_vals, name="Rolling correlation",
            line=dict(color="#1565C0", width=2.5),
            fill="tozeroy", fillcolor="rgba(21,101,192,0.1)",
        ))
        fig_roll.add_hline(y=0,       line_dash="dot", line_color="#333", line_width=0.8)
        fig_roll.add_hline(y=sig_thr,  line_dash="dash", line_color="#C5A028",
                            annotation_text=f"+95% sig ({sig_thr:.2f})")
        fig_roll.add_hline(y=-sig_thr, line_dash="dash", line_color="#C5A028",
                            annotation_text=f"-95% sig (-{sig_thr:.2f})")
        fig_roll.update_layout(
            height=320, margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,248,248,0.5)",
            xaxis=dict(title="Year (end of 10-yr window)"),
            yaxis=dict(title="Pearson r", range=[-1.1, 1.1]),
        )
        st.plotly_chart(fig_roll, use_container_width=True)

    # ── Cross-correlation ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Cross-Correlation — Lead/Lag Structure")
    st.info(corr.get("lead_lag_plain", ""))

    lags   = corr.get("lags",   [])
    xcorr  = corr.get("xcorr",  [])
    sig_t  = corr.get("sig_threshold", 0.27)

    if lags and xcorr:
        bar_colours = ["#8B0000" if v < -sig_t else "#006400" if v > sig_t else "#CCCCCC"
                       for v in xcorr]
        fig_xc = go.Figure()
        fig_xc.add_trace(go.Bar(x=lags, y=xcorr, marker_color=bar_colours,
                                 name="Cross-correlation"))
        fig_xc.add_hline(y=sig_t,  line_dash="dash", line_color="#333",
                          annotation_text=f"+95% sig ({sig_t:.2f})")
        fig_xc.add_hline(y=-sig_t, line_dash="dash", line_color="#333",
                          annotation_text=f"-95% sig")
        fig_xc.add_vline(x=0, line_dash="dot", line_color="#555")
        peak_lag = corr.get("peak_lag", 0)
        fig_xc.add_vline(x=peak_lag, line_color="#C5A028", line_width=2,
                          annotation_text=f"Peak lag={peak_lag}")
        fig_xc.update_layout(
            height=320, margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,248,248,0.5)",
            xaxis=dict(title="Lag (years)  |  Negative = inflation leads  |  Positive = rates lead"),
            yaxis=dict(title="Pearson r"),
        )
        st.plotly_chart(fig_xc, use_container_width=True)

    # ── Fisher Effect ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Fisher Effect Test")
    st.info(corr.get("fisher_plain", ""))
    f1, f2, f3 = st.columns(3)
    with f1: st.metric("OLS Slope",   f"{corr.get('fisher_slope', 'N/A'):.4f}",
                        delta="Expected: 1.00 (Fisher Effect)")
    with f2: st.metric("R-squared",   f"{corr.get('fisher_r_squared', 'N/A'):.4f}")
    with f3: st.metric("Fisher Holds", "Yes" if corr.get("fisher_holds") else "No")

    # ── Decade correlations ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Decade-by-Decade Correlations")
    decade_corr = corr.get("decade_corr", {})
    if decade_corr:
        rows = []
        for decade, vals in decade_corr.items():
            rows.append({
                "Decade":      f"{decade}s",
                "Pearson r":   vals.get("pearson_r", "N/A"),
                "p-value":     vals.get("p_value",   "N/A"),
                "Significant": "Yes" if vals.get("significant") else "No",
                "N obs":       vals.get("n_obs",     "N/A"),
            })
        df_dec = pd.DataFrame(rows)
        st.dataframe(df_dec, use_container_width=True, hide_index=True)