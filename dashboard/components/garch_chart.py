# ─────────────────────────────────────────────────────────────────────────────
# IRIS — GARCH Chart Component
# Reusable GARCH volatility visualisation.
# ─────────────────────────────────────────────────────────────────────────────

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


def garch_volatility_chart(garch_result: dict,
                            inflation_series: list = None,
                            years: list = None,
                            height: int = 380) -> go.Figure:
    """
    Render the GARCH conditional volatility chart.
    Optionally overlays the actual inflation series.

    INPUT:
        garch_result      — dict from models.garch.run_garch()
        inflation_series  — optional list of inflation values
        years             — list of year values
        height            — chart height

    OUTPUT: Plotly Figure
    """
    if not garch_result or garch_result.get("error"):
        fig = go.Figure()
        fig.add_annotation(text="GARCH data unavailable",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=14, color="#999"))
        fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)")
        return fig

    cond_vol  = garch_result.get("cond_vol",  [])
    g_years   = years or garch_result.get("years", list(range(len(cond_vol))))
    hist_avg  = garch_result.get("historical_avg_vol", 0)
    peak_yrs  = garch_result.get("peak_vol_years",  [])
    peak_vals = garch_result.get("peak_vol_values", [])
    cur_vol   = garch_result.get("current_vol", 0)

    rows    = 2 if (inflation_series and len(inflation_series) == len(g_years)) else 1
    row_h   = [0.5, 0.5] if rows == 2 else [1.0]
    subtitles = (
        ["Inflation (actual)", "Conditional Volatility (GARCH)"]
        if rows == 2 else
        ["Conditional Volatility — How Unpredictable Has Inflation Been?"]
    )

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        row_heights=row_h,
        subplot_titles=subtitles,
        vertical_spacing=0.08,
    )

    if rows == 2:
        # Top: actual inflation
        fig.add_trace(go.Scatter(
            x=g_years, y=inflation_series,
            name="Inflation",
            line=dict(color="#8B0000", width=2),
            hovertemplate="<b>%{x}</b>: %{y:.2f}%<extra>Inflation</extra>",
        ), row=1, col=1)

        fig.add_hrect(y0=2.5, y1=7.5, fillcolor="#006400",
                      opacity=0.07, row=1, col=1)
        fig.update_yaxes(title_text="Inflation (%)", row=1, col=1)

    # Bottom (or only): volatility
    vol_row = 2 if rows == 2 else 1

    # Colour code by risk level vs average
    bar_colours = [
        "#8B0000" if v > hist_avg * 1.5 else
        "#E65100" if v > hist_avg * 1.1 else
        "#C5A028" if v > hist_avg * 0.9 else
        "#006400"
        for v in cond_vol
    ]

    fig.add_trace(go.Bar(
        x=g_years, y=cond_vol,
        name="Volatility",
        marker_color=bar_colours,
        opacity=0.75,
        hovertemplate="<b>%{x}</b>: volatility = %{y:.2f}pp<extra></extra>",
    ), row=vol_row, col=1)

    fig.add_trace(go.Scatter(
        x=g_years, y=cond_vol,
        mode="lines",
        line=dict(color="#C5A028", width=1.5),
        showlegend=False,
        hoverinfo="skip",
    ), row=vol_row, col=1)

    # Historical average line
    if hist_avg:
        fig.add_hline(
            y=hist_avg,
            line_dash="dash", line_color="#555", line_width=1.2,
            annotation_text=f"Avg: {hist_avg:.2f}pp",
            annotation_position="right",
            row=vol_row, col=1,
        )

    # Annotate peak years
    for yr, val in zip(peak_yrs[:3], peak_vals[:3]):
        fig.add_annotation(
            x=yr, y=val,
            text=str(int(yr)),
            showarrow=True, arrowhead=2,
            font=dict(color="#8B0000", size=9),
            row=vol_row, col=1,
        )

    # Current vol reference line
    if cur_vol and g_years:
        fig.add_annotation(
            x=g_years[-1], y=cur_vol,
            text=f"Now: {cur_vol:.2f}",
            showarrow=False,
            font=dict(color="#1565C0", size=9, weight="bold"),
            xanchor="left",
            row=vol_row, col=1,
        )

    fig.update_layout(
        height=height,
        margin=dict(t=40, b=20, l=20, r=80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,248,0.5)",
        showlegend=False,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Volatility (pp)", row=vol_row, col=1)
    fig.update_xaxes(title_text="Year", row=vol_row, col=1)

    return fig