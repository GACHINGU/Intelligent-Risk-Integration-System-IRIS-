# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Reusable Gauge Component
# The IRIS Risk Score gauge. Import and call anywhere in the dashboard.
# ─────────────────────────────────────────────────────────────────────────────

import plotly.graph_objects as go


def iris_gauge(score: float, colour: str,
               height: int = 300,
               show_delta: bool = True) -> go.Figure:
    """
    Build the IRIS Risk Score gauge figure.

    INPUT:
        score      — float 0-100
        colour     — hex colour string for the current regime
        height     — chart height in pixels
        show_delta — whether to show delta vs 50 (midpoint)

    OUTPUT: Plotly Figure object — pass to st.plotly_chart()
    """
    mode = "gauge+number+delta" if show_delta else "gauge+number"

    fig = go.Figure(go.Indicator(
        mode  = mode,
        value = score,
        title = {
            "text": "IRIS Risk Score",
            "font": {"size": 16, "color": "#003300"},
        },
        delta = {
            "reference":   50,
            "increasing":  {"color": "#8B0000"},
            "decreasing":  {"color": "#006400"},
        } if show_delta else None,
        gauge = {
            "axis": {
                "range":     [0, 100],
                "tickwidth": 1,
                "tickcolor": "#003300",
                "tickvals":  [0, 25, 50, 75, 100],
                "ticktext":  ["0", "25", "50", "75", "100"],
            },
            "bar": {"color": colour, "thickness": 0.3},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "#CCCCCC",
            "steps": [
                {"range": [0,  25], "color": "#C8E6C9"},   # Stable — green
                {"range": [25, 50], "color": "#FFF9C4"},   # Moderate — yellow
                {"range": [50, 75], "color": "#FFE0B2"},   # Danger — orange
                {"range": [75,100], "color": "#FFCDD2"},   # Critical — red
            ],
            "threshold": {
                "line":      {"color": colour, "width": 5},
                "thickness": 0.8,
                "value":     score,
            },
        },
        number = {
            "suffix": "/100",
            "font":   {"size": 38, "color": colour},
        },
    ))

    fig.update_layout(
        height          = height,
        margin          = dict(t=40, b=10, l=20, r=20),
        paper_bgcolor   = "rgba(0,0,0,0)",
        font            = {"family": "Arial"},
    )
    return fig


def mini_gauge(score: float, colour: str, height: int = 160) -> go.Figure:
    """
    A compact gauge for use in tight spaces (e.g. sidebar or card).
    """
    fig = go.Figure(go.Indicator(
        mode  = "gauge+number",
        value = score,
        gauge = {
            "axis": {"range": [0, 100], "visible": False},
            "bar":  {"color": colour, "thickness": 0.4},
            "steps": [
                {"range": [0,  25], "color": "#C8E6C9"},
                {"range": [25, 50], "color": "#FFF9C4"},
                {"range": [50, 75], "color": "#FFE0B2"},
                {"range": [75,100], "color": "#FFCDD2"},
            ],
        },
        number = {"suffix": "/100", "font": {"size": 22, "color": colour}},
    ))
    fig.update_layout(
        height=height,
        margin=dict(t=10, b=5, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig