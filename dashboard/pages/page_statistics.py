# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Statistics Page
# Full statistical summary — every number the system computes.
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats


def render(iris: dict):
    features = iris["features"]
    models   = iris["model_results"]

    st.markdown("## 📈 Full Statistics Panel")
    st.markdown("Every statistic computed by IRIS in one place.")

    tab1, tab2, tab3 = st.tabs([
        "📊 Descriptive Statistics",
        "🔢 Model Parameters",
        "📋 Raw Data Table",
    ])

    # ── TAB 1: Descriptive ────────────────────────────────────────────────────
    with tab1:
        st.markdown("### Descriptive Statistics — Interest Rate & Inflation")

        def full_stats(series, name):
            s = series.dropna()
            skew_val = float(s.skew())
            kurt_val = float(s.kurtosis())
            sw_stat, sw_p = scipy_stats.shapiro(s)
            return {
                "Series":          name,
                "N":               len(s),
                "Mean":            round(s.mean(),   3),
                "Median":          round(s.median(), 3),
                "Std Dev":         round(s.std(),    3),
                "Min":             round(s.min(),    3),
                "Max":             round(s.max(),    3),
                "10th Pct":        round(s.quantile(0.10), 3),
                "25th Pct":        round(s.quantile(0.25), 3),
                "75th Pct":        round(s.quantile(0.75), 3),
                "90th Pct":        round(s.quantile(0.90), 3),
                "Skewness":        round(skew_val, 4),
                "Kurtosis":        round(kurt_val, 4),
                "Shapiro-Wilk p":  round(sw_p, 4),
                "Normal?":         "Yes" if sw_p >= 0.05 else "No",
            }

        rows = [
            full_stats(features["interest_rate"], "Interest Rate"),
            full_stats(features["inflation"],     "Inflation"),
            full_stats(features["real_rate"],     "Real Interest Rate"),
        ]
        df_desc = pd.DataFrame(rows).set_index("Series")
        st.dataframe(df_desc.T, use_container_width=True)

        st.markdown("---")
        st.markdown("### Distribution Plots")
        import plotly.figure_factory as ff

        col_a, col_b = st.columns(2)
        with col_a:
            ir_clean = features["interest_rate"].dropna().tolist()
            fig_dist = ff.create_distplot([ir_clean], ["Interest Rate"],
                                           colors=["#006400"], show_rug=False)
            fig_dist.update_layout(
                height=280, title="Interest Rate Distribution",
                margin=dict(t=40, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_dist, use_container_width=True)
        with col_b:
            inf_clean = features["inflation"].dropna().tolist()
            fig_dist2 = ff.create_distplot([inf_clean], ["Inflation"],
                                            colors=["#8B0000"], show_rug=False)
            fig_dist2.update_layout(
                height=280, title="Inflation Distribution",
                margin=dict(t=40, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_dist2, use_container_width=True)

    # ── TAB 2: Model Parameters ───────────────────────────────────────────────
    with tab2:
        st.markdown("### Model Parameters Summary")

        sections = {
            "Cointegration (Johansen)": {
                "Rank":          models.get("cointegration", {}).get("rank",        "N/A"),
                "Cointegrated":  models.get("cointegration", {}).get("cointegrated","N/A"),
                "Optimal Lags":  models.get("cointegration", {}).get("optimal_lag", "N/A"),
                "E-G statistic": models.get("cointegration", {}).get("eg_statistic","N/A"),
                "E-G p-value":   models.get("cointegration", {}).get("eg_p_value",  "N/A"),
            },
            "VECM": {
                "Alpha IR":           models.get("vecm", {}).get("alpha_ir",         "N/A"),
                "Alpha Inflation":    models.get("vecm", {}).get("alpha_inf",        "N/A"),
                "Beta Inflation":     models.get("vecm", {}).get("beta_inflation",   "N/A"),
                "Policy Character":   models.get("vecm", {}).get("policy_character", "N/A"),
                "Half-Life (yrs)":    models.get("vecm", {}).get("half_life_years",  "N/A"),
            },
            "IRF": {
                "First Negative Year": models.get("irf", {}).get("first_negative_year", "N/A"),
                "Peak Year":           models.get("irf", {}).get("peak_year",           "N/A"),
                "Peak Value":          models.get("irf", {}).get("peak_value",          "N/A"),
                "Price Puzzle":        models.get("irf", {}).get("price_puzzle",        "N/A"),
                "Cumulative 5yr":      models.get("irf", {}).get("cumulative_5yr",      "N/A"),
                "Cumulative 10yr":     models.get("irf", {}).get("cumulative_10yr",     "N/A"),
            },
            "FEVD (Long-Run)": {
                "IR Explains Inflation": f"{models.get('fevd', {}).get('ir_share_lr',   'N/A')}%",
                "Own Explains Inflation":f"{models.get('fevd', {}).get('own_share_lr',  'N/A')}%",
                "CBK Autonomy":          f"{models.get('fevd', {}).get('cbk_autonomy',  'N/A')}%",
                "CBK Reactive Share":    f"{models.get('fevd', {}).get('cbk_reactive_share','N/A')}%",
                "Policy Power":          models.get("fevd", {}).get("policy_power",     "N/A"),
            },
            "GARCH(1,1)": {
                "Mu (mean)":         models.get("garch", {}).get("mu",                "N/A"),
                "Alpha (ARCH)":      models.get("garch", {}).get("alpha",             "N/A"),
                "Beta (GARCH)":      models.get("garch", {}).get("beta",              "N/A"),
                "Persistence":       models.get("garch", {}).get("persistence",       "N/A"),
                "Current Vol":       models.get("garch", {}).get("current_vol",       "N/A"),
                "Historical Avg Vol":models.get("garch", {}).get("historical_avg_vol","N/A"),
                "Vol Ratio":         models.get("garch", {}).get("vol_ratio",         "N/A"),
                "Risk Level":        models.get("garch", {}).get("garch_risk",        "N/A"),
            },
            "Regime Switching": {
                "Current Regime":    models.get("regime", {}).get("current_regime",    "N/A"),
                "P(High)":           models.get("regime", {}).get("current_p_high",    "N/A"),
                "P(Stay High)":      models.get("regime", {}).get("p_stay_high",       "N/A"),
                "P(Low → High)":     models.get("regime", {}).get("p_low_to_high",     "N/A"),
                "Duration High (yr)":models.get("regime", {}).get("duration_high_yrs", "N/A"),
                "Mean (High)":       models.get("regime", {}).get("mean_high_regime",  "N/A"),
                "Mean (Low)":        models.get("regime", {}).get("mean_low_regime",   "N/A"),
                "Signal":            models.get("regime", {}).get("regime_signal",     "N/A"),
            },
            "Correlations": {
                "Pearson r":         models.get("correlations", {}).get("pearson_r",       "N/A"),
                "Spearman ρ":        models.get("correlations", {}).get("spearman_r",      "N/A"),
                "Rolling Corr":      models.get("correlations", {}).get("current_roll_corr","N/A"),
                "Corr Trend":        models.get("correlations", {}).get("corr_trend",      "N/A"),
                "Peak Lag":          models.get("correlations", {}).get("peak_lag",        "N/A"),
                "Fisher Slope":      models.get("correlations", {}).get("fisher_slope",    "N/A"),
                "Fisher Holds":      models.get("correlations", {}).get("fisher_holds",    "N/A"),
            },
        }

        for section_name, params in sections.items():
            with st.expander(section_name, expanded=False):
                rows = [{"Parameter": k, "Value": str(v)} for k, v in params.items()]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── TAB 3: Raw Data ───────────────────────────────────────────────────────
    with tab3:
        st.markdown("### Raw Data Table — All Features")
        cols_to_show = [
            "year", "interest_rate", "inflation", "real_rate",
            "d_inflation", "d_interest_rate", "roll10_inf_mean", "roll10_inf_std",
            "roll10_ir_mean", "roll10_corr", "above_target", "stress_raw",
        ]
        cols_to_show = [c for c in cols_to_show if c in features.columns]
        df_show = features[cols_to_show].copy().round(4)
        st.dataframe(df_show, use_container_width=True, height=500)

        csv = df_show.to_csv(index=False)
        st.download_button(
            label="⬇️ Download as CSV",
            data=csv,
            file_name="iris_data_export.csv",
            mime="text/csv",
        )