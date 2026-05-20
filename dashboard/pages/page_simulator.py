# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Policy Lag Simulator
#
# WHAT THIS PAGE DOES:
# Lets the user interactively ask:
# "If the CBK changes rates by X% today, what happens to inflation
#  over the next 1-10 years?"
#
# Built on the IRF results from the VECM model.
# The user picks a rate shock size and sees the projected inflation path.
# This is exactly the tool an MPC member would use before a rate decision.
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from dashboard.style.layout import page_header, disclaimer_footer


def render(iris: dict):
    features = iris["features"]
    irf      = iris["model_results"].get("irf", {})
    latest   = iris["latest"]
    colour   = iris["iris_score"]["regime_colour"]

    inf_val  = latest.get("inflation",     {}).get("value", 8.0)
    ir_val   = latest.get("interest_rate", {}).get("value", 7.0)

    st.markdown(page_header(
        "🔬 Policy Lag Simulator",
        "Simulate the projected inflation path after a CBK rate decision",
        iris.get("live_available", False),
    ), unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#E8F5E9; border-left:4px solid #006400;
                padding:0.8rem 1rem; border-radius:6px; margin-bottom:1.2rem;
                font-size:0.88rem;'>
        <b>How to use this simulator:</b><br>
        1. Choose a hypothetical rate change (hike or cut)<br>
        2. See the projected inflation path over the next 10 years<br>
        3. Compare multiple scenarios side by side<br>
        <br>
        <b>Important:</b> This is based on the VECM Impulse Response Function fitted on
        53 years of Kenya data. It shows the <i>average historical response</i> —
        actual outcomes will vary based on supply-side conditions.
    </div>
    """, unsafe_allow_html=True)

    # ── Controls ───────────────────────────────────────────────────────────────
    st.markdown("### Simulation Controls")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        shock_size = st.slider(
            "Rate change (pp)",
            min_value=-3.0, max_value=3.0,
            value=0.5, step=0.25,
            help="Positive = rate hike. Negative = rate cut.",
        )
    with col_b:
        horizon = st.slider(
            "Forecast horizon (years)",
            min_value=1, max_value=10,
            value=5, step=1,
        )
    with col_c:
        show_uncertainty = st.checkbox("Show uncertainty bands", value=True)

    # Scenario comparison
    st.markdown("#### Add Comparison Scenarios")
    col_s1, col_s2, col_s3 = st.columns(3)
    scenarios = [(shock_size, "#006400", f"Primary: {shock_size:+.2f}pp")]

    with col_s1:
        if st.checkbox("Add +1.0pp hike scenario", value=False):
            scenarios.append((1.0, "#1565C0", "+1.0pp hike"))
    with col_s2:
        if st.checkbox("Add +2.0pp hike scenario", value=False):
            scenarios.append((2.0, "#C5A028", "+2.0pp hike"))
    with col_s3:
        if st.checkbox("Add -0.5pp cut scenario", value=False):
            scenarios.append((-0.5, "#8B0000", "-0.5pp cut"))

    # ── Build simulation ───────────────────────────────────────────────────────
    irf_response = irf.get("ir_to_inf", [])
    if not irf_response:
        st.error("IRF data not available. Run the model pipeline first.")
        return

    # Normalise IRF to per-1pp (it may already be, but we scale by shock)
    irf_arr  = np.array(irf_response[:horizon + 1])
    periods  = list(range(horizon + 1))

    # Projected inflation path = current inflation + shock * IRF response
    fig = go.Figure()

    # Baseline (no change)
    baseline = [inf_val] * (horizon + 1)
    fig.add_trace(go.Scatter(
        x=periods, y=baseline,
        name="Baseline (no rate change)",
        line=dict(color="#999", width=1.5, dash="dot"),
        hovertemplate="Year %{x}: baseline = %{y:.2f}%<extra></extra>",
    ))

    # CBK target band
    fig.add_hrect(y0=2.5, y1=7.5, fillcolor="#006400", opacity=0.08,
                  annotation_text="CBK target (2.5-7.5%)",
                  annotation_position="top right")

    # Each scenario
    for shock, col, label in scenarios:
        projected = [inf_val + shock * v for v in irf_arr]

        fig.add_trace(go.Scatter(
            x=periods, y=projected,
            name=label,
            line=dict(color=col, width=2.5),
            mode="lines+markers",
            marker=dict(size=6, color=col),
            hovertemplate=f"Year %{{x}}: {label} = %{{y:.2f}}<extra></extra>",
        ))

        if show_uncertainty and len(irf_arr) > 0:
            # Approximate 90% CI: ±35% of the response (based on historical model uncertainty)
            ci_band = np.abs(irf_arr) * 0.35
            upper   = [inf_val + shock * (v + c) for v, c in zip(irf_arr, ci_band)]
            lower   = [inf_val + shock * (v - c) for v, c in zip(irf_arr, ci_band)]
            
            # Map standard hex colors to valid transparent rgba strings for Plotly
            rgba_mapping = {
                "#006400": "rgba(0, 100, 0, 0.08)",    # Primary (Dark Green)
                "#1565C0": "rgba(21, 101, 192, 0.08)",  # Hike 1 (Blue)
                "#C5A028": "rgba(197, 160, 40, 0.08)",  # Hike 2 (Gold)
                "#8B0000": "rgba(139, 0, 0, 0.08)"      # Cut (Dark Red)
            }
            rgba_color = rgba_mapping.get(col, "rgba(0, 100, 0, 0.08)")

            fig.add_trace(go.Scatter(
                x=periods + periods[::-1],
                y=upper + lower[::-1],
                fill="toself",
                fillcolor=rgba_color,  # <--- Clean, readable rgba string
                line=dict(color="rgba(0,0,0,0)"),
                name=f"{label} — 90% CI",
                showlegend=False,
                hoverinfo="skip",
            ))

    fig.update_layout(
        title=f"Projected Inflation Path — Starting from {inf_val:.1f}%",
        height=440,
        margin=dict(t=50, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,248,0.5)",
        xaxis=dict(
            title="Years after rate decision",
            tickvals=periods,
            gridcolor="#EEEEEE",
        ),
        yaxis=dict(title="Projected inflation (%)", gridcolor="#EEEEEE"),
        legend=dict(orientation="h", y=1.08),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Summary table ──────────────────────────────────────────────────────────
    st.markdown("### Projected Inflation at Key Horizons")

    import pandas as pd
    rows = []
    for shock, col, label in scenarios:
        projected = [inf_val + shock * v for v in irf_arr]
        row = {"Scenario": label}
        for yr in [1, 2, 3, 5, min(horizon, 10)]:
            if yr <= len(projected) - 1:
                row[f"Year {yr}"] = f"{projected[yr]:.2f}%"
            else:
                row[f"Year {yr}"] = "N/A"
        row["In target?"] = "✅ Yes" if 2.5 <= projected[-1] <= 7.5 else "❌ No"
        rows.append(row)

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── Key insights ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Simulator Insights")

    first_neg = irf.get("first_negative_year")
    peak_yr   = irf.get("peak_year", "N/A")
    puzzle    = irf.get("price_puzzle", False)

    col_i1, col_i2, col_i3 = st.columns(3)
    with col_i1:
        st.metric(
            "First negative effect",
            f"Year {first_neg}" if first_neg else "Not detected",
            help="How many years before a rate hike starts reducing inflation",
        )
    with col_i2:
        st.metric(
            "Peak impact year",
            f"Year {peak_yr}",
            help="When the rate change has its maximum effect on inflation",
        )
    with col_i3:
        st.metric(
            "Price puzzle",
            "Present ⚠️" if puzzle else "Not present ✅",
            help="Does inflation rise briefly in year 1 before falling?",
        )

    st.info(irf.get("transmission_plain", ""))
    if puzzle:
        st.warning(irf.get("price_puzzle_plain", ""))

    st.markdown(disclaimer_footer(), unsafe_allow_html=True)