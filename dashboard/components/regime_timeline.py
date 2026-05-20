# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Regime Timeline Component
# Visualises the Markov regime probabilities over time.
# Shows when Kenya was in high vs low inflation regimes.
# ─────────────────────────────────────────────────────────────────────────────

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


def regime_probability_chart(years: list,
                               prob_high: list,
                               inflation: list = None,
                               height: int = 380) -> go.Figure:
    """
    Render a two-panel regime probability chart.

    TOP panel:    inflation series with regime shading
    BOTTOM panel: P(high-inflation regime) over time

    INPUT:
        years      — list of year values
        prob_high  — list of P(high-inflation regime) at each year
        inflation  — optional list of inflation values for top panel
        height     — total chart height

    OUTPUT: Plotly Figure
    """
    rows      = 2 if inflation else 1
    row_h     = [0.55, 0.45] if inflation else [1.0]
    subtitles = (
        ["Inflation with Regime Shading", "P(High-Inflation Regime)"]
        if inflation else
        ["P(High-Inflation Regime)"]
    )

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        row_heights=row_h,
        subplot_titles=subtitles,
        vertical_spacing=0.08,
    )

    if inflation and len(inflation) == len(years):
        # ── Top panel: inflation ───────────────────────────────────────────────
        fig.add_trace(go.Scatter(
            x=years, y=inflation,
            name="Inflation",
            line=dict(color="#8B0000", width=2),
            hovertemplate="<b>%{x}</b>: %{y:.2f}%<extra>Inflation</extra>",
        ), row=1, col=1)

        # Regime shading on top panel
        for i in range(len(years) - 1):
            colour = "rgba(139,0,0,0.12)" if prob_high[i] > 0.5 else "rgba(0,100,0,0.07)"
            fig.add_vrect(
                x0=years[i], x1=years[i + 1],
                fillcolor=colour, line_width=0,
                row=1, col=1,
            )

        # CBK target band
        fig.add_hrect(
            y0=2.5, y1=7.5, fillcolor="#006400", opacity=0.07,
            annotation_text="CBK target",
            annotation_position="top right",
            row=1, col=1,
        )

    # ── Bottom panel (or only panel): regime probability ──────────────────────
    bottom_row = 2 if inflation else 1

    fig.add_trace(go.Scatter(
        x=years, y=prob_high,
        name="P(High-inflation)",
        line=dict(color="#8B0000", width=2),
        fill="tozeroy",
        fillcolor="rgba(139,0,0,0.15)",
        hovertemplate="<b>%{x}</b>: P(high) = %{y:.2%}<extra></extra>",
    ), row=bottom_row, col=1)

    # 50% threshold line
    fig.add_hline(
        y=0.5,
        line_dash="dash",
        line_color="#333",
        line_width=1,
        annotation_text="50% threshold",
        annotation_position="right",
        row=bottom_row, col=1,
    )

    fig.update_layout(
        height=height,
        margin=dict(t=40, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,248,0.5)",
        showlegend=False,
        hovermode="x unified",
    )

    # Y-axis labels
    if inflation:
        fig.update_yaxes(title_text="Inflation (%)", row=1, col=1)
    fig.update_yaxes(
        title_text="P(High regime)",
        range=[0, 1.05],
        tickformat=".0%",
        row=bottom_row, col=1,
    )
    fig.update_xaxes(title_text="Year", row=bottom_row, col=1)

    return fig


def regime_transition_card(regime_result: dict) -> str:
    """
    Build an HTML card showing regime transition probabilities.
    Returns HTML string for st.markdown(unsafe_allow_html=True).
    """
    p_stay_low    = regime_result.get("p_stay_low",    0)
    p_low_to_high = regime_result.get("p_low_to_high", 0)
    p_stay_high   = regime_result.get("p_stay_high",   0)
    p_high_to_low = regime_result.get("p_high_to_low", 0)
    dur_low       = regime_result.get("duration_low_yrs",  0)
    dur_high      = regime_result.get("duration_high_yrs", 0)

    return f"""
    <div style='background:#F5F5F5; border-radius:8px; padding:1rem; font-size:0.85rem;'>
        <div style='font-weight:bold; color:#003300; margin-bottom:0.6rem;'>
            Regime Transition Matrix
        </div>
        <table style='width:100%; border-collapse:collapse;'>
            <tr style='background:#003300; color:white;'>
                <th style='padding:6px; text-align:left;'>From → To</th>
                <th style='padding:6px; text-align:center;'>Low Inflation</th>
                <th style='padding:6px; text-align:center;'>High Inflation</th>
            </tr>
            <tr style='background:#C8E6C9;'>
                <td style='padding:6px; font-weight:bold; color:#006400;'>Low Inflation</td>
                <td style='padding:6px; text-align:center;'>
                    <b>{p_stay_low*100:.0f}%</b><br>
                    <span style='font-size:0.75rem; color:#666;'>stay ({dur_low:.1f} yr avg)</span>
                </td>
                <td style='padding:6px; text-align:center;'>
                    <b style='color:#8B0000;'>{p_low_to_high*100:.0f}%</b><br>
                    <span style='font-size:0.75rem; color:#666;'>switch</span>
                </td>
            </tr>
            <tr style='background:#FFCDD2;'>
                <td style='padding:6px; font-weight:bold; color:#8B0000;'>High Inflation</td>
                <td style='padding:6px; text-align:center;'>
                    <b style='color:#006400;'>{p_high_to_low*100:.0f}%</b><br>
                    <span style='font-size:0.75rem; color:#666;'>exit</span>
                </td>
                <td style='padding:6px; text-align:center;'>
                    <b style='color:#8B0000;'>{p_stay_high*100:.0f}%</b><br>
                    <span style='font-size:0.75rem; color:#666;'>stay ({dur_high:.1f} yr avg)</span>
                </td>
            </tr>
        </table>
        <div style='margin-top:0.6rem; font-size:0.78rem; color:#777;'>
            <b>Key insight:</b> Once Kenya enters the high-inflation regime,
            there is a {p_stay_high*100:.0f}% chance of staying there next year.
            Exit requires sustained policy tightening.
        </div>
    </div>
    """