# ─────────────────────────────────────────────────────────────────────────────
# IRIS — IRF Chart Component
# Reusable Impulse Response Function chart.
# ─────────────────────────────────────────────────────────────────────────────

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


def irf_chart(irf_result: dict, height: int = 400) -> go.Figure:
    """
    Render the full two-panel IRF chart.

    LEFT:  Rate shock → Inflation response
    RIGHT: Inflation shock → Rate response

    INPUT:  irf_result — dict from models.irf.run_irf()
    OUTPUT: Plotly Figure
    """
    if not irf_result or irf_result.get("error"):
        fig = go.Figure()
        fig.add_annotation(text="IRF data unavailable",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=14, color="#999"))
        fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)")
        return fig

    periods    = list(range(irf_result.get("periods", 10) + 1))
    ir_to_inf  = irf_result.get("ir_to_inf",  [0] * 11)
    inf_to_ir  = irf_result.get("inf_to_ir",  [0] * 11)
    peak_yr    = irf_result.get("peak_year",   0)
    cbk_peak   = irf_result.get("cbk_peak_year", 0)
    puzzle     = irf_result.get("price_puzzle", False)

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "If CBK raises rates by 1% → What happens to inflation?",
            "If inflation spikes by 1% → How does CBK respond?",
        ),
    )

    # ── LEFT: Rate → Inflation ────────────────────────────────────────────────
    bar_colours_l = [
        "#8B0000" if v > 0 else "#006400"
        for v in ir_to_inf
    ]
    fig.add_trace(go.Bar(
        x=periods, y=ir_to_inf,
        name="Inflation response",
        marker_color=bar_colours_l,
        opacity=0.7,
        hovertemplate="Year %{x}: %{y:.4f}pp<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=periods, y=ir_to_inf,
        mode="lines+markers",
        line=dict(color="#006400", width=2),
        marker=dict(size=6, color="#006400"),
        showlegend=False,
        hoverinfo="skip",
    ), row=1, col=1)

    fig.add_hline(y=0, line_dash="dot", line_color="#999", line_width=0.8, row=1, col=1)

    if peak_yr is not None and peak_yr < len(periods):
        fig.add_vline(
            x=peak_yr,
            line_dash="dash", line_color="#C5A028", line_width=1.5,
            annotation_text=f"Peak yr {peak_yr}",
            annotation_position="top",
            row=1, col=1,
        )

    if puzzle:
        fig.add_annotation(
            x=1, y=max(ir_to_inf[:3]) if ir_to_inf else 0.1,
            text="⚠️ Price puzzle",
            showarrow=False,
            font=dict(size=9, color="#8B0000"),
            row=1, col=1,
        )

    # ── RIGHT: Inflation → Rate ────────────────────────────────────────────────
    bar_colours_r = [
        "#006400" if v > 0 else "#8B0000"
        for v in inf_to_ir
    ]
    fig.add_trace(go.Bar(
        x=periods, y=inf_to_ir,
        name="Rate response",
        marker_color=bar_colours_r,
        opacity=0.7,
        hovertemplate="Year %{x}: %{y:.4f}pp<extra></extra>",
    ), row=1, col=2)

    fig.add_trace(go.Scatter(
        x=periods, y=inf_to_ir,
        mode="lines+markers",
        line=dict(color="#8B0000", width=2),
        marker=dict(size=6, color="#8B0000"),
        showlegend=False,
        hoverinfo="skip",
    ), row=1, col=2)

    fig.add_hline(y=0, line_dash="dot", line_color="#999", line_width=0.8, row=1, col=2)

    if cbk_peak is not None and cbk_peak < len(periods):
        fig.add_vline(
            x=cbk_peak,
            line_dash="dash", line_color="#C5A028", line_width=1.5,
            annotation_text=f"CBK peak yr {cbk_peak}",
            annotation_position="top",
            row=1, col=2,
        )

    fig.update_layout(
        height=height,
        margin=dict(t=50, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,248,0.5)",
        showlegend=False,
        hovermode="x",
    )
    fig.update_xaxes(title_text="Years after shock")
    fig.update_yaxes(title_text="Change (%)", col=1)
    fig.update_yaxes(title_text="Change (%)", col=2)

    return fig


def irf_cumulative_chart(irf_result: dict, height: int = 300) -> go.Figure:
    """
    Render the cumulative IRF — total effect of rate hike on inflation over time.
    """
    if not irf_result or irf_result.get("error"):
        return go.Figure()

    ir_to_inf = irf_result.get("ir_to_inf", [])
    periods   = list(range(len(ir_to_inf)))

    import numpy as np
    cumulative = list(np.cumsum(ir_to_inf))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=periods, y=cumulative,
        name="Cumulative effect",
        line=dict(color="#1565C0", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(21,101,192,0.1)",
        hovertemplate="After %{x} years: cumulative = %{y:.4f}pp<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="#999")

    fig.update_layout(
        title="Cumulative Inflation Effect of 1pp Rate Hike",
        height=height,
        margin=dict(t=40, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,248,0.5)",
        xaxis=dict(title="Years after rate hike"),
        yaxis=dict(title="Cumulative change in inflation (pp)"),
    )
    return fig