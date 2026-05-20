# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Sparkline Component
# Tiny inline trend charts. Used in the home page and live data page
# to show recent trend without a full chart.
# ─────────────────────────────────────────────────────────────────────────────

import plotly.graph_objects as go
import pandas as pd
import numpy as np


def sparkline(values: list,
              colour: str = "#006400",
              height: int = 80,
              show_last: bool = True) -> go.Figure:
    """
    Render a minimal sparkline chart.

    INPUT:
        values    — list of numeric values (most recent last)
        colour    — line colour hex string
        height    — chart height in pixels
        show_last — annotate the last value

    OUTPUT: Plotly Figure object
    """
    x = list(range(len(values)))
    y = [float(v) for v in values]

    fig = go.Figure()

    # Fill area
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines",
        line=dict(color=colour, width=2),
        fill="tozeroy",
        fillcolor=colour.replace("#", "rgba(").rstrip(")") + ",0.1)"
                  if colour.startswith("#") else colour,
        hoverinfo="skip",
    ))

    # Last value dot
    if show_last and y:
        fig.add_trace(go.Scatter(
            x=[x[-1]], y=[y[-1]],
            mode="markers",
            marker=dict(color=colour, size=7),
            hoverinfo="skip",
        ))

    fig.update_layout(
        height=height,
        margin=dict(t=2, b=2, l=2, r=2),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def trend_sparkline(series: pd.Series,
                    n_last: int = 15,
                    colour: str = "#006400",
                    height: int = 80) -> go.Figure:
    """
    Build a sparkline from the last n_last values of a pandas Series.
    """
    recent = series.dropna().tail(n_last).tolist()
    return sparkline(recent, colour=colour, height=height)


def delta_colour(current: float, previous: float,
                 higher_is_good: bool = False) -> str:
    """
    Return a colour based on whether the change is positive or negative.

    higher_is_good=True  → green if rising (e.g. real rate)
    higher_is_good=False → green if falling (e.g. inflation)
    """
    if current > previous:
        return "#006400" if higher_is_good else "#8B0000"
    elif current < previous:
        return "#8B0000" if higher_is_good else "#006400"
    return "#555555"