# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Centralised Visual Theme
#
# All colours, fonts, spacing, and chart styles live here.
# Import from this file instead of hardcoding values in pages.
# Change once here — updates everywhere.
# ─────────────────────────────────────────────────────────────────────────────

# ── Colour Palette ────────────────────────────────────────────────────────────
COLOURS = {
    # CBK brand
    "cbk_dark":       "#003300",
    "cbk_green":      "#006400",
    "cbk_light":      "#E8F5E9",
    "cbk_mid":        "#1B5E20",
    "gold":           "#C5A028",

    # Risk levels
    "stable":         "#006400",
    "moderate":       "#C5A028",
    "danger":         "#E65100",
    "critical":       "#8B0000",

    # Series colours
    "interest_rate":  "#006400",
    "inflation":      "#8B0000",
    "real_rate":      "#1565C0",
    "volatility":     "#C5A028",
    "regime":         "#8B0000",

    # UI
    "background":     "#FAFAFA",
    "surface":        "#FFFFFF",
    "border":         "#CCCCCC",
    "text_dark":      "#1A1A1A",
    "text_mid":       "#555555",
    "text_light":     "#AAAAAA",
    "light_grey":     "#F5F5F5",
    "warning_bg":     "#FFF3E0",
    "critical_bg":    "#FFEBEE",
    "info_bg":        "#E3F2FD",
}

# ── Risk Level Metadata ────────────────────────────────────────────────────────
RISK_META = {
    "STABLE": {
        "colour":  "#006400",
        "bg":      "#E8F5E9",
        "emoji":   "🟢",
        "label":   "STABLE",
    },
    "MODERATE": {
        "colour":  "#C5A028",
        "bg":      "#FFF9C4",
        "emoji":   "🟡",
        "label":   "MODERATE",
    },
    "DANGER": {
        "colour":  "#E65100",
        "bg":      "#FFE0B2",
        "emoji":   "🟠",
        "label":   "DANGER",
    },
    "CRITICAL": {
        "colour":  "#8B0000",
        "bg":      "#FFCDD2",
        "emoji":   "🔴",
        "label":   "CRITICAL",
    },
}

# ── Severity Metadata ─────────────────────────────────────────────────────────
SEVERITY_META = {
    "CRITICAL": {"icon": "🔴", "bg": "#FFEBEE", "colour": "#8B0000"},
    "ALERT":    {"icon": "🟠", "bg": "#FFF3E0", "colour": "#E65100"},
    "WARNING":  {"icon": "🟡", "bg": "#FFFDE7", "colour": "#C5A028"},
    "INFO":     {"icon": "🔵", "bg": "#E3F2FD", "colour": "#1565C0"},
}

# ── Chart Defaults ─────────────────────────────────────────────────────────────
CHART = {
    "height_small":   260,
    "height_medium":  360,
    "height_large":   460,
    "margin":         dict(t=30, b=20, l=20, r=20),
    "paper_bgcolor":  "rgba(0,0,0,0)",
    "plot_bgcolor":   "rgba(248,248,248,0.5)",
    "gridcolor":      "#EEEEEE",
    "font_family":    "Arial",
}

# ── Plotly Layout Base ─────────────────────────────────────────────────────────
def base_layout(height=None, title=None):
    """Return a base Plotly layout dict."""
    layout = {
        "paper_bgcolor": CHART["paper_bgcolor"],
        "plot_bgcolor":  CHART["plot_bgcolor"],
        "margin":        CHART["margin"],
        "font":          {"family": CHART["font_family"]},
        "xaxis":         {"gridcolor": CHART["gridcolor"]},
        "yaxis":         {"gridcolor": CHART["gridcolor"]},
    }
    if height:
        layout["height"] = height
    if title:
        layout["title"] = {"text": title, "font": {"color": COLOURS["cbk_dark"]}}
    return layout

# ── Streamlit CSS ──────────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
    /* Page background */
    .main { background-color: #FAFAFA; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #003300;
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #CCFFCC !important;
        font-size: 0.88rem;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #E8F5E9;
        border-left: 4px solid #006400;
        padding: 10px 14px;
        border-radius: 6px;
    }
    div[data-testid="stMetric"] label {
        color: #003300 !important;
        font-size: 0.78rem;
    }

    /* Headers */
    h1, h2, h3 { color: #003300; }
    h1 { font-size: 1.6rem; }
    h2 { font-size: 1.3rem; }
    h3 { font-size: 1.1rem; }

    /* Remove top padding */
    .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }

    /* Tab styling */
    .stTabs [data-baseweb="tab"] {
        font-size: 0.85rem;
        padding: 6px 14px;
    }
    .stTabs [aria-selected="true"] {
        color: #006400;
        border-bottom-color: #006400;
    }

    /* Info / warning / error boxes */
    .iris-box {
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin: 0.4rem 0;
        font-size: 0.88rem;
        line-height: 1.5;
    }
    .iris-stable   { background: #E8F5E9; border-left: 4px solid #006400; }
    .iris-moderate { background: #FFF9C4; border-left: 4px solid #C5A028; }
    .iris-danger   { background: #FFE0B2; border-left: 4px solid #E65100; }
    .iris-critical { background: #FFCDD2; border-left: 4px solid #8B0000; }

    /* Download button */
    .stDownloadButton button {
        background-color: #006400;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 0.85rem;
    }
    .stDownloadButton button:hover {
        background-color: #004D00;
    }

    /* Dataframe */
    .stDataFrame { border-radius: 6px; overflow: hidden; }

    /* Expander */
    .streamlit-expanderHeader {
        font-size: 0.88rem;
        color: #003300;
        font-weight: bold;
    }
</style>
"""

# ── Helper: Coloured box HTML ──────────────────────────────────────────────────
def risk_box(title: str, body: str, regime: str = "MODERATE") -> str:
    """Return HTML for a coloured risk box."""
    meta = RISK_META.get(regime.upper(), RISK_META["MODERATE"])
    return f"""
    <div style='background:{meta["bg"]}; border-left:4px solid {meta["colour"]};
                padding:0.8rem 1rem; border-radius:6px; margin:0.4rem 0;'>
        <div style='font-weight:bold; color:{meta["colour"]}; font-size:0.88rem;'>
            {meta["emoji"]} {title}
        </div>
        <div style='font-size:0.85rem; color:#333; margin-top:0.3rem; line-height:1.5;'>
            {body}
        </div>
    </div>
    """


def severity_box(title: str, body: str, severity: str = "WARNING") -> str:
    """Return HTML for a severity-coloured alert box."""
    meta = SEVERITY_META.get(severity.upper(), SEVERITY_META["WARNING"])
    return f"""
    <div style='background:{meta["bg"]}; border-left:4px solid {meta["colour"]};
                padding:0.7rem 1rem; border-radius:6px; margin:0.4rem 0;'>
        <div style='font-weight:bold; color:{meta["colour"]}; font-size:0.82rem;'>
            {meta["icon"]} {severity} — {title}
        </div>
        <div style='font-size:0.82rem; color:#333; margin-top:0.2rem; line-height:1.5;'>
            {body}
        </div>
    </div>
    """


def stat_card(value: str, label: str, colour: str = "#006400") -> str:
    """Return HTML for a stat card."""
    return f"""
    <div style='text-align:center; background:{colour}18;
                border:1px solid {colour}; border-radius:8px;
                padding:0.8rem 0.4rem;'>
        <div style='font-size:1.5rem; font-weight:bold; color:{colour};'>{value}</div>
        <div style='font-size:0.72rem; color:#555; margin-top:0.2rem; line-height:1.3;'>{label}</div>
    </div>
    """