# ─────────────────────────────────────────────────────────────────────────────
# IRIS — FEVD Chart Component
# Reusable Forecast Error Variance Decomposition charts.
# ─────────────────────────────────────────────────────────────────────────────

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def fevd_stacked_chart(fevd_result: dict, height: int = 360) -> go.Figure:
    """
    Render the FEVD as two stacked area charts side by side.

    LEFT:  What drives INFLATION uncertainty?
    RIGHT: What drives INTEREST RATE uncertainty?

    INPUT:  fevd_result — dict from models.fevd.run_fevd()
    OUTPUT: Plotly Figure
    """
    if not fevd_result or fevd_result.get("error"):
        fig = go.Figure()
        fig.add_annotation(text="FEVD data unavailable",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=14, color="#999"))
        fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)")
        return fig

    periods       = fevd_result.get("periods", 12)
    horizons      = list(range(1, periods + 1))

    inf_ir  = [v * 100 for v in fevd_result.get("fevd_inf_from_ir",  [0.14] * periods)]
    inf_own = [v * 100 for v in fevd_result.get("fevd_inf_from_own", [0.86] * periods)]
    ir_own  = [v * 100 for v in fevd_result.get("fevd_ir_from_own",  [0.60] * periods)]
    ir_inf  = [v * 100 for v in fevd_result.get("fevd_ir_from_inf",  [0.40] * periods)]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "What drives INFLATION uncertainty?",
            "What drives INTEREST RATE uncertainty?",
        ),
    )

    # ── LEFT: Inflation FEVD ──────────────────────────────────────────────────
    fig.add_trace(go.Bar(
        x=horizons, y=inf_ir,
        name="From CBK rate decisions",
        marker_color="#006400", opacity=0.85,
        hovertemplate="Year %{x}: %{y:.1f}% from IR<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=horizons, y=inf_own,
        name="From supply shocks (food, fuel, FX)",
        marker_color="#CCCCCC", opacity=0.75,
        hovertemplate="Year %{x}: %{y:.1f}% from supply<extra></extra>",
    ), row=1, col=1)

    # Annotate long-run IR share
    lr_ir = fevd_result.get("ir_share_lr", 14)
    fig.add_annotation(
        x=horizons[-1] * 0.6, y=lr_ir / 2,
        text=f"{lr_ir:.0f}%<br>from CBK",
        showarrow=False,
        font=dict(color="white", size=11, weight="bold"),
        row=1, col=1,
    )

    # ── RIGHT: Interest Rate FEVD ─────────────────────────────────────────────
    fig.add_trace(go.Bar(
        x=horizons, y=ir_own,
        name="From IR own shocks (autonomous CBK)",
        marker_color="#006400", opacity=0.75,
        showlegend=False,
        hovertemplate="Year %{x}: %{y:.1f}% autonomous<extra></extra>",
    ), row=1, col=2)

    fig.add_trace(go.Bar(
        x=horizons, y=ir_inf,
        name="From inflation shocks (reactive CBK)",
        marker_color="#8B0000", opacity=0.75,
        showlegend=False,
        hovertemplate="Year %{x}: %{y:.1f}% from inflation<extra></extra>",
    ), row=1, col=2)

    fig.update_layout(
        barmode="stack",
        height=height,
        margin=dict(t=50, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,248,0.5)",
        legend=dict(orientation="h", y=-0.15),
        hovermode="x",
    )
    fig.update_xaxes(title_text="Years ahead (forecast horizon)")
    fig.update_yaxes(title_text="%", range=[0, 100])

    return fig


def fevd_pie_chart(ir_share: float, height: int = 280) -> go.Figure:
    """
    Render a simple donut pie showing CBK vs supply-side share.

    INPUT:
        ir_share — % of inflation explained by CBK rates (0-100)
        height   — chart height

    OUTPUT: Plotly Figure
    """
    own_share = 100 - ir_share

    fig = go.Figure(go.Pie(
        labels=["CBK Interest Rate Policy", "Supply-Side Shocks\n(food, fuel, FX, drought)"],
        values=[ir_share, own_share],
        hole=0.5,
        marker_colors=["#006400", "#CCCCCC"],
        textfont_size=12,
        hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        height=height,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text=f"{ir_share:.0f}%<br><span style='font-size:10px'>CBK</span>",
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False,
            font_color="#006400",
        )],
        showlegend=True,
        legend=dict(orientation="h", y=-0.1),
    )
    return fig