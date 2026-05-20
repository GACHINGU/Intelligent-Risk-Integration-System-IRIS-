# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Models Page
# Shows all 8 model outputs with charts and plain-English interpretation.
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


def render(iris: dict):
    models   = iris["model_results"]
    features = iris["features"]

    st.markdown("## 🤖 Structural Models — Deep Analysis")
    st.markdown("""
    <div style='background:#E8F5E9; border-left:4px solid #006400;
                padding:0.8rem 1rem; border-radius:6px; margin-bottom:1rem;
                font-size:0.88rem;'>
        All 8 structural models are run on every data refresh.
        Each model answers a specific policy question about Kenya's monetary dynamics.
        Results are explained in plain English alongside the technical output.
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔗 VECM & Cointegration",
        "⚡ Impulse Response",
        "📊 FEVD",
        "📈 GARCH Volatility",
        "🔄 Regime Switching",
        "🧪 Stationarity",
    ])

    # ── TAB 1: VECM & Cointegration ───────────────────────────────────────────
    with tab1:
        coint = models.get("cointegration", {})
        vecm  = models.get("vecm", {})

        st.markdown("### Cointegration — Are Rates and Inflation Leashed Together?")
        c1, c2, c3 = st.columns(3)
        with c1:
            rank = coint.get("rank", "N/A")
            st.metric("Johansen Rank", rank,
                      delta="Cointegrated" if coint.get("cointegrated") else "Not cointegrated")
        with c2:
            st.metric("Model Choice", coint.get("model_choice", "N/A"))
        with c3:
            st.metric("Optimal Lags", coint.get("optimal_lag", "N/A"))

        st.info(coint.get("plain_english", ""))
        st.markdown(coint.get("interpretation", ""))

        st.markdown("---")
        st.markdown("### VECM — Short-Run Dynamics & Long-Run Correction")

        v1, v2, v3, v4 = st.columns(4)
        with v1:
            st.metric("Alpha (IR)", f"{vecm.get('alpha_ir', 'N/A'):.4f}" if vecm.get('alpha_ir') else "N/A",
                      help="Speed at which interest rate corrects to equilibrium")
        with v2:
            st.metric("Alpha (Inflation)", f"{vecm.get('alpha_inf', 'N/A'):.4f}" if vecm.get('alpha_inf') else "N/A",
                      help="Speed at which inflation corrects to equilibrium")
        with v3:
            st.metric("Policy Character", vecm.get("policy_character", "N/A"))
        with v4:
            hl = vecm.get("half_life_years")
            st.metric("Half-Life", f"{hl:.1f} yrs" if hl else "N/A",
                      help="Years before half of a deviation from equilibrium is corrected")

        st.markdown(f"**Long-Run Relationship:** {vecm.get('lr_plain', '')}")
        st.markdown(f"**Policy Character:** {vecm.get('policy_plain', '')}")
        st.markdown(f"**Half-Life:** {vecm.get('half_life_plain', '')}")

    # ── TAB 2: IRF ────────────────────────────────────────────────────────────
    with tab2:
        irf = models.get("irf", {})
        if irf.get("error"):
            st.error(f"IRF error: {irf['error']}")
        else:
            st.markdown("### Impulse Response Functions")
            st.markdown("""
            **How to read this chart:**
            - LEFT: If CBK raises rates by 1% today, what happens to inflation over 10 years?
            - RIGHT: If inflation spikes by 1%, how does the CBK respond?
            """)

            periods     = list(range(irf.get("periods", 10) + 1))
            ir_to_inf   = irf.get("ir_to_inf",  [0]*11)
            inf_to_ir   = irf.get("inf_to_ir",  [0]*11)

            fig = make_subplots(rows=1, cols=2,
                subplot_titles=(
                    "Rate Hike → Inflation Response<br><sub>If CBK raises rates by 1%, what happens to inflation?</sub>",
                    "Inflation Spike → Rate Response<br><sub>If inflation rises 1%, how does CBK respond?</sub>",
                ))

            fig.add_trace(go.Scatter(
                x=periods, y=ir_to_inf, name="Inflation response",
                line=dict(color="#006400", width=2.5),
                mode="lines+markers", marker=dict(size=6),
                fill="tozeroy", fillcolor="rgba(0,100,0,0.08)",
            ), row=1, col=1)
            fig.add_hline(y=0, line_dash="dot", line_color="#999", row=1, col=1)

            # Highlight peak impact
            peak_yr  = irf.get("peak_year", 0)
            peak_val = irf.get("peak_value", 0)
            if peak_yr is not None and peak_yr < len(periods):
                fig.add_vline(x=peak_yr, line_dash="dash", line_color="#C5A028",
                              annotation_text=f"Peak: year {peak_yr}",
                              annotation_position="top", row=1, col=1)

            fig.add_trace(go.Scatter(
                x=periods, y=inf_to_ir, name="Rate response",
                line=dict(color="#8B0000", width=2.5),
                mode="lines+markers", marker=dict(size=6),
                fill="tozeroy", fillcolor="rgba(139,0,0,0.08)",
            ), row=1, col=2)
            fig.add_hline(y=0, line_dash="dot", line_color="#999", row=1, col=2)

            fig.update_layout(
                height=380, margin=dict(t=50, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(248,248,248,0.5)",
                xaxis=dict(title="Years after shock"),
                xaxis2=dict(title="Years after shock"),
                yaxis=dict(title="Change in inflation (%)"),
                yaxis2=dict(title="Change in interest rate (%)"),
            )
            st.plotly_chart(fig, use_container_width=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Transmission:** {irf.get('transmission_plain', '')}")
                st.markdown(f"**Price puzzle:** {irf.get('price_puzzle_plain', '')}")
            with col_b:
                st.markdown(f"**CBK response:** {irf.get('cbk_response_plain', '')}")
                fn = irf.get("first_negative_year")
                cum5  = irf.get("cumulative_5yr",  "N/A")
                cum10 = irf.get("cumulative_10yr", "N/A")
                st.metric("First negative response", f"Year {fn}" if fn else "Not detected")
                st.metric("Cumulative 5yr effect", f"{cum5:.3f}%" if isinstance(cum5, float) else "N/A")

    # ── TAB 3: FEVD ───────────────────────────────────────────────────────────
    with tab3:
        fevd = models.get("fevd", {})
        if fevd.get("error"):
            st.error(f"FEVD error: {fevd['error']}")
        else:
            st.markdown("### Forecast Error Variance Decomposition")
            st.markdown("**The Inflation Pie:** What % of Kenya's inflation uncertainty comes from CBK rate decisions vs supply-side shocks?")

            ir_share = fevd.get("ir_share_lr",   14)
            own_share = fevd.get("own_share_lr",  86)

            col_pie, col_bar = st.columns(2)
            with col_pie:
                fig_pie = go.Figure(go.Pie(
                    labels=["CBK Interest Rate Policy", "Supply-Side Shocks\n(food, fuel, FX, drought)"],
                    values=[ir_share, own_share],
                    hole=0.45,
                    marker_colors=["#006400", "#CCCCCC"],
                    textfont_size=13,
                ))
                fig_pie.update_layout(
                    height=300, margin=dict(t=10, b=10, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    annotations=[dict(text=f"{ir_share:.0f}%<br>CBK",
                                      x=0.5, y=0.5, font_size=14, showarrow=False,
                                      font_color="#006400")],
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_bar:
                horizons  = list(range(1, fevd.get("periods", 12) + 1))
                ir_series = [v*100 for v in fevd.get("fevd_inf_from_ir",  [0.14]*12)]
                own_series = [v*100 for v in fevd.get("fevd_inf_from_own", [0.86]*12)]

                fig_fevd = go.Figure()
                fig_fevd.add_trace(go.Bar(x=horizons, y=ir_series,  name="From IR shocks",
                                          marker_color="#006400", opacity=0.85))
                fig_fevd.add_trace(go.Bar(x=horizons, y=own_series, name="From own shocks",
                                          marker_color="#CCCCCC", opacity=0.85))
                fig_fevd.update_layout(
                    barmode="stack", height=300,
                    margin=dict(t=10, b=10, l=10, r=10),
                    xaxis=dict(title="Years ahead"),
                    yaxis=dict(title="%", range=[0, 100]),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(248,248,248,0.5)",
                    legend=dict(orientation="h", y=1.1),
                )
                st.plotly_chart(fig_fevd, use_container_width=True)

            st.info(fevd.get("policy_plain", ""))
            st.info(fevd.get("supply_plain", ""))

            f1, f2, f3 = st.columns(3)
            with f1: st.metric("IR explains (1yr)",  f"{fevd.get('ir_share_1yr',  'N/A')}%")
            with f2: st.metric("IR explains (5yr)",  f"{fevd.get('ir_share_5yr',  'N/A')}%")
            with f3: st.metric("IR explains (LR)",   f"{fevd.get('ir_share_lr',   'N/A')}%")

    # ── TAB 4: GARCH ──────────────────────────────────────────────────────────
    with tab4:
        garch = models.get("garch", {})
        if garch.get("error"):
            st.error(f"GARCH error: {garch['error']}")
        else:
            st.markdown("### GARCH(1,1) — Inflation Volatility Over Time")
            st.markdown("How unpredictable has Kenya's inflation been at each point in time? Taller peaks = harder to plan.")

            g1, g2, g3, g4 = st.columns(4)
            with g1: st.metric("Current Volatility",    f"{garch.get('current_vol', 'N/A'):.2f}pp")
            with g2: st.metric("Historical Avg",        f"{garch.get('historical_avg_vol', 'N/A'):.2f}pp")
            with g3: st.metric("Ratio",                 f"{garch.get('vol_ratio', 'N/A'):.2f}x")
            with g4: st.metric("Persistence (α+β)",     f"{garch.get('persistence', 'N/A'):.4f}")

            cond_vol = garch.get("cond_vol", [])
            garch_years = garch.get("years", [])

            if cond_vol and garch_years:
                fig_g = go.Figure()
                fig_g.add_trace(go.Scatter(
                    x=garch_years, y=cond_vol,
                    name="Conditional Volatility",
                    line=dict(color="#C5A028", width=2),
                    fill="tozeroy", fillcolor="rgba(197,160,40,0.15)",
                ))
                avg_vol = garch.get("historical_avg_vol", 0)
                if avg_vol:
                    fig_g.add_hline(y=avg_vol, line_dash="dash", line_color="#8B0000",
                                    annotation_text=f"Historical avg ({avg_vol:.2f})")

                # Annotate peak years
                for yr, val in zip(garch.get("peak_vol_years", []),
                                   garch.get("peak_vol_values", [])):
                    fig_g.add_annotation(x=yr, y=val, text=str(int(yr)),
                                         showarrow=True, arrowhead=2,
                                         font=dict(color="#8B0000", size=10))

                fig_g.update_layout(
                    height=360, margin=dict(t=20, b=20, l=20, r=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(248,248,248,0.5)",
                    xaxis=dict(title="Year"),
                    yaxis=dict(title="Conditional Volatility (pp)"),
                )
                st.plotly_chart(fig_g, use_container_width=True)

            risk_col = {"LOW": "success", "MODERATE": "info",
                        "ELEVATED": "warning", "HIGH": "error"}.get(
                garch.get("garch_risk", "MODERATE"), "info")
            getattr(st, risk_col)(garch.get("garch_risk_plain", ""))
            st.info(garch.get("persistence_plain", ""))

    # ── TAB 5: Regime Switching ───────────────────────────────────────────────
    with tab5:
        regime = models.get("regime", {})
        if regime.get("error"):
            st.error(f"Regime Switching error: {regime['error']}")
        else:
            st.markdown("### Markov Regime-Switching — High vs Low Inflation Eras")
            st.markdown("When was Kenya in a high-inflation 'stressed' regime vs a stable low-inflation regime?")

            r1, r2, r3, r4 = st.columns(4)
            with r1: st.metric("Current Regime", regime.get("current_regime", "N/A"))
            with r2: st.metric("P(High-Inflation)", f"{regime.get('current_p_high', 0)*100:.0f}%")
            with r3: st.metric("P(Stay High)",     f"{regime.get('p_stay_high', 0)*100:.0f}%")
            with r4: st.metric("Expected Duration", f"{regime.get('duration_high_yrs', 'N/A'):.1f} yrs")

            prob_high   = regime.get("prob_high", [])
            reg_years   = regime.get("years", [])
            inf_for_reg = features["inflation"].values[:len(prob_high)]

            if prob_high and reg_years:
                fig_reg = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    subplot_titles=("Inflation with Regime Shading",
                                    "P(High-Inflation Regime)"),
                    row_heights=[0.6, 0.4])

                fig_reg.add_trace(go.Scatter(
                    x=reg_years, y=inf_for_reg[:len(reg_years)],
                    name="Inflation", line=dict(color="#8B0000", width=2),
                ), row=1, col=1)
                fig_reg.add_hrect(y0=2.5, y1=7.5, fillcolor="#006400",
                                  opacity=0.08, row=1, col=1)

                fig_reg.add_trace(go.Scatter(
                    x=reg_years, y=prob_high,
                    name="P(High regime)",
                    line=dict(color="#8B0000", width=2),
                    fill="tozeroy", fillcolor="rgba(139,0,0,0.15)",
                ), row=2, col=1)
                fig_reg.add_hline(y=0.5, line_dash="dash", line_color="#333",
                                  annotation_text="50% threshold", row=2, col=1)

                fig_reg.update_layout(
                    height=450, margin=dict(t=30, b=20, l=20, r=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(248,248,248,0.5)",
                )
                st.plotly_chart(fig_reg, use_container_width=True)

            sig_map = {"STABLE": "success", "MODERATE": "info",
                       "DANGER": "warning",  "CRITICAL": "error"}
            getattr(st, sig_map.get(regime.get("regime_signal", "MODERATE"), "info"))(
                regime.get("regime_plain", ""))
            st.info(regime.get("persistence_plain", ""))

            tran_data = {
                "Transition": ["Low → Low (stay)", "Low → High (switch)",
                               "High → High (stay)", "High → Low (exit)"],
                "Probability": [
                    f"{regime.get('p_stay_low',    0)*100:.1f}%",
                    f"{regime.get('p_low_to_high', 0)*100:.1f}%",
                    f"{regime.get('p_stay_high',   0)*100:.1f}%",
                    f"{regime.get('p_high_to_low', 0)*100:.1f}%",
                ],
                "Duration (yrs)": ["N/A", "N/A",
                                    f"{regime.get('duration_high_yrs', 'N/A'):.1f}",
                                    f"{regime.get('duration_low_yrs',  'N/A'):.1f}"],
            }
            import pandas as pd
            st.dataframe(pd.DataFrame(tran_data), use_container_width=True, hide_index=True)

    # ── TAB 6: Stationarity ───────────────────────────────────────────────────
    with tab6:
        stat = models.get("stationarity", {})
        st.markdown("### Stationarity Tests — ADF + KPSS")
        st.markdown("Is each series stable (stationary) or does it drift without a fixed level to return to?")

        import pandas as pd
        rows = []
        for key, res in stat.items():
            if not isinstance(res, dict): continue
            adf  = res.get("adf",  {})
            kpss = res.get("kpss", {})
            rows.append({
                "Series":             res.get("series", key),
                "ADF Statistic":      adf.get("statistic",     "N/A"),
                "ADF p-value":        adf.get("p_value",       "N/A"),
                "ADF Verdict":        adf.get("verdict",       "N/A"),
                "KPSS Statistic":     kpss.get("statistic",    "N/A"),
                "KPSS p-value":       kpss.get("p_value",      "N/A"),
                "KPSS Verdict":       kpss.get("verdict",      "N/A"),
                "Combined Verdict":   res.get("combined",      "N/A"),
                "Integration Order":  res.get("integration",   "N/A"),
            })
        if rows:
            df_stat = pd.DataFrame(rows)
            st.dataframe(df_stat, use_container_width=True, hide_index=True)
            st.caption("ADF H0: series is non-stationary. KPSS H0: series is stationary. Both tests used as cross-check.")