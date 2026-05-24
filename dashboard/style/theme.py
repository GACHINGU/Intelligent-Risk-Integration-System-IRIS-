# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Visual Theme (redesigned)
# Uses semantic colour tokens properly. Works in light and dark mode.
# No hardcoded text-on-background colours.
# ─────────────────────────────────────────────────────────────────────────────

# ── Plotly chart colours ───────────────────────────────────────────────────────
# These are safe mid-tones that read on both white and dark chart backgrounds
PLOT = {
    "interest_rate": "#2563EB",   # Blue 600
    "inflation":     "#DC2626",   # Red 600
    "real_rate":     "#0891B2",   # Teal 600
    "volatility":    "#D97706",   # Amber 600
    "regime":        "#7C3AED",   # Purple 600
    "neutral":       "#6B7280",   # Gray 500
    "target":        "#16A34A",   # Green 600
    "target_fill":   "rgba(22,163,74,0.08)",
}

# ── Risk level colours ─────────────────────────────────────────────────────────
# Border/accent colour only — never use as background for text
RISK = {
    "STABLE":   {"accent": "#16A34A", "bg": "#F0FDF4", "text": "#14532D", "emoji": "🟢"},
    "MODERATE": {"accent": "#D97706", "bg": "#FFFBEB", "text": "#78350F", "emoji": "🟡"},
    "DANGER":   {"accent": "#EA580C", "bg": "#FFF7ED", "text": "#7C2D12", "emoji": "🟠"},
    "CRITICAL": {"accent": "#DC2626", "bg": "#FEF2F2", "text": "#7F1D1D", "emoji": "🔴"},
}

# ── Severity colours ───────────────────────────────────────────────────────────
SEVERITY = {
    "CRITICAL": {"bg": "#FEF2F2", "border": "#DC2626", "text": "#7F1D1D", "icon": "🔴"},
    "ALERT":    {"bg": "#FFF7ED", "border": "#EA580C", "text": "#7C2D12", "icon": "🟠"},
    "WARNING":  {"bg": "#FFFBEB", "border": "#D97706", "text": "#78350F", "icon": "🟡"},
    "INFO":     {"bg": "#EFF6FF", "border": "#2563EB", "text": "#1E3A8A", "icon": "🔵"},
}

# ── Plotly chart defaults ──────────────────────────────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    margin        = dict(t=32, b=24, l=8, r=8),
    font          = dict(family="system-ui, -apple-system, sans-serif", size=12),
    xaxis         = dict(
        gridcolor     = "rgba(107,114,128,0.15)",
        linecolor     = "rgba(107,114,128,0.2)",
        tickcolor     = "rgba(107,114,128,0.4)",
        tickfont      = dict(size=11),
        title_font    = dict(size=12),
    ),
    yaxis         = dict(
        gridcolor     = "rgba(107,114,128,0.15)",
        linecolor     = "rgba(107,114,128,0.2)",
        tickcolor     = "rgba(107,114,128,0.4)",
        tickfont      = dict(size=11),
        title_font    = dict(size=12),
    ),
    legend        = dict(
        bgcolor       = "rgba(0,0,0,0)",
        bordercolor   = "rgba(0,0,0,0)",
        font          = dict(size=11),
        orientation   = "h",
        y             = 1.04,
        x             = 0,
    ),
    hoverlabel    = dict(
        bgcolor     = "rgba(17,24,39,0.9)",
        bordercolor = "rgba(0,0,0,0)",
        font        = dict(color="#F9FAFB", size=12),
    ),
)


def chart_layout(**overrides) -> dict:
    """Return a base Plotly layout dict with optional overrides."""
    layout = dict(CHART_LAYOUT)
    layout["xaxis"] = dict(CHART_LAYOUT["xaxis"])
    layout["yaxis"] = dict(CHART_LAYOUT["yaxis"])
    layout.update(overrides)
    return layout


# ── Streamlit global CSS ───────────────────────────────────────────────────────
# Uses Streamlit's own CSS variables wherever possible.
# Never puts light text on light backgrounds.
GLOBAL_CSS = """
<style>
/* ── Sidebar ────────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #0F172A;
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] .stRadio label {
    color: #94A3B8 !important;
    font-size: 0.875rem;
    padding: 0.25rem 0;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    color: #F1F5F9 !important;
}
section[data-testid="stSidebar"] [aria-checked="true"] + div label {
    color: #F1F5F9 !important;
    font-weight: 500;
}
section[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    color: #E2E8F0;
    width: 100%;
    border-radius: 8px;
    padding: 0.4rem 0.8rem;
    font-size: 0.85rem;
    cursor: pointer;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,0.12);
}

/* ── Page layout ────────────────────────────────────────────────────────────── */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px;
}
.main > div { background: transparent; }

/* ── Metric cards ───────────────────────────────────────────────────────────── */
div[data-testid="stMetric"] {
    background: var(--background-color);
    border: 1px solid rgba(107,114,128,0.2);
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
}
div[data-testid="stMetric"] > label {
    font-size: 0.75rem !important;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    opacity: 0.6;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 600;
    letter-spacing: -0.02em;
}

/* ── Tabs ───────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab"] {
    font-size: 0.875rem;
    font-weight: 500;
    padding: 0.5rem 1rem;
}
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid rgba(107,114,128,0.2);
    gap: 0;
}

/* ── Expander ───────────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    font-size: 0.875rem;
    font-weight: 500;
    border-radius: 8px;
}

/* ── Download button ────────────────────────────────────────────────────────── */
.stDownloadButton button {
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 500;
}

/* ── Dataframe ──────────────────────────────────────────────────────────────── */
.stDataFrame { border-radius: 10px; overflow: hidden; }
.stDataFrame iframe { border-radius: 10px; }

/* ── Remove top padding on headers ─────────────────────────────────────────── */
h1, h2, h3 { font-weight: 600; letter-spacing: -0.01em; }
h1 { font-size: 1.5rem; }
h2 { font-size: 1.25rem; }
h3 { font-size: 1.05rem; }

/* ── Info/warning/error overrides ───────────────────────────────────────────── */
.stAlert { border-radius: 10px; }
</style>
"""


# ── HTML component helpers ─────────────────────────────────────────────────────
# All return HTML strings safe for st.markdown(unsafe_allow_html=True)
# Text is ALWAYS dark-on-light — no white text on coloured backgrounds
# except the sidebar (which is intentionally dark)

def score_badge(score: float, regime: str) -> str:
    """Large centred IRIS score badge."""
    r = RISK.get(regime, RISK["MODERATE"])
    return f"""
<div style="
    display:flex; flex-direction:column; align-items:center;
    background:{r['bg']}; border:2px solid {r['accent']};
    border-radius:16px; padding:1.5rem 1rem; text-align:center;
">
    <div style="font-size:3rem; font-weight:700; color:{r['text']}; line-height:1;">
        {score:.0f}
    </div>
    <div style="font-size:0.75rem; color:{r['text']}; opacity:0.7;
                margin-top:0.25rem; font-weight:500; text-transform:uppercase;
                letter-spacing:0.06em;">
        out of 100
    </div>
    <div style="margin-top:0.6rem; font-size:1rem; font-weight:600; color:{r['text']};">
        {r['emoji']} {regime}
    </div>
</div>"""


def risk_pill(regime: str) -> str:
    """Inline regime pill/badge."""
    r = RISK.get(regime, RISK["MODERATE"])
    return (f'<span style="background:{r["bg"]}; color:{r["text"]}; '
            f'border:1px solid {r["accent"]}; border-radius:99px; '
            f'font-size:0.78rem; font-weight:600; padding:2px 10px;">'
            f'{r["emoji"]} {regime}</span>')


def section_header(title: str, subtitle: str = "") -> str:
    """Page section header with optional subtitle."""
    sub = (f'<p style="margin:0.2rem 0 0; font-size:0.875rem; '
           f'color:var(--text-color); opacity:0.55; font-weight:400;">'
           f'{subtitle}</p>') if subtitle else ""
    return f"""
<div style="border-bottom:2px solid rgba(107,114,128,0.15);
            padding-bottom:0.75rem; margin-bottom:1.25rem;">
    <h2 style="margin:0; font-size:1.2rem; font-weight:600;">{title}</h2>
    {sub}
</div>"""


def info_box(body: str, style: str = "info") -> str:
    """Coloured callout box. style = info|success|warning|danger"""
    colours = {
        "info":    ("#EFF6FF", "#BFDBFE", "#1E3A8A"),
        "success": ("#F0FDF4", "#BBF7D0", "#14532D"),
        "warning": ("#FFFBEB", "#FDE68A", "#78350F"),
        "danger":  ("#FEF2F2", "#FECACA", "#7F1D1D"),
    }
    bg, border, text = colours.get(style, colours["info"])
    return f"""
<div style="background:{bg}; border-left:4px solid {border};
            border-radius:0 8px 8px 0; padding:0.75rem 1rem;
            margin:0.5rem 0; font-size:0.875rem; color:{text}; line-height:1.6;">
    {body}
</div>"""


def warning_card_html(flag: str, message: str, severity: str = "WARNING") -> str:
    """Alert/warning card with proper contrast."""
    s = SEVERITY.get(severity, SEVERITY["WARNING"])
    return f"""
<div style="background:{s['bg']}; border-left:4px solid {s['border']};
            border-radius:0 8px 8px 0; padding:0.7rem 1rem;
            margin-bottom:0.5rem;">
    <div style="font-weight:600; font-size:0.8rem; color:{s['text']};
                margin-bottom:0.2rem; text-transform:uppercase; letter-spacing:0.04em;">
        {s['icon']} {severity} — {flag}
    </div>
    <div style="font-size:0.85rem; color:{s['text']}; opacity:0.85; line-height:1.5;">
        {message}
    </div>
</div>"""


def signal_card_html(sig_type: str, action: str,
                     detail: str, priority: int) -> str:
    """Policy signal card with proper contrast."""
    type_styles = {
        "RATE_ACTION":   ("#FEF2F2", "#DC2626", "#7F1D1D"),
        "RISK_FLAG":     ("#FFF7ED", "#EA580C", "#7C2D12"),
        "MONITORING":    ("#FFFBEB", "#D97706", "#78350F"),
        "COORDINATION":  ("#EFF6FF", "#2563EB", "#1E3A8A"),
        "COMMUNICATION": ("#F0FDF4", "#16A34A", "#14532D"),
    }
    bg, border, text = type_styles.get(sig_type, ("#F9FAFB", "#6B7280", "#374151"))
    return f"""
<div style="background:{bg}; border-left:4px solid {border};
            border-radius:0 8px 8px 0; padding:0.75rem 1rem; margin-bottom:0.5rem;">
    <div style="display:flex; justify-content:space-between; align-items:center;
                margin-bottom:0.3rem;">
        <span style="font-size:0.75rem; font-weight:600; color:{text};
                     text-transform:uppercase; letter-spacing:0.05em;">
            {sig_type.replace('_',' ')}
        </span>
        <span style="font-size:0.72rem; color:{text}; opacity:0.6;">
            Priority {priority}
        </span>
    </div>
    <div style="font-size:0.9rem; font-weight:600; color:{text};
                margin-bottom:0.25rem;">{action}</div>
    <div style="font-size:0.82rem; color:{text}; opacity:0.75;
                line-height:1.5;">{detail}</div>
</div>"""


def metric_row(items: list) -> str:
    """
    Horizontal row of stat cards.
    items = list of (value, label, optional_delta, optional_delta_colour)
    """
    cards = []
    for item in items:
        value = item[0]
        label = item[1]
        delta = item[2] if len(item) > 2 else None
        delta_col = item[3] if len(item) > 3 else "#6B7280"
        delta_html = (
            f'<div style="font-size:0.72rem; color:{delta_col}; '
            f'margin-top:0.2rem; font-weight:500;">{delta}</div>'
        ) if delta else ""
        cards.append(f"""
<div style="background:var(--background-color);
            border:1px solid rgba(107,114,128,0.18);
            border-radius:10px; padding:0.9rem 1rem; flex:1; min-width:0;">
    <div style="font-size:0.72rem; font-weight:500; opacity:0.55;
                text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.3rem;">
        {label}
    </div>
    <div style="font-size:1.5rem; font-weight:700; letter-spacing:-0.02em;">
        {value}
    </div>
    {delta_html}
</div>""")

    return (f'<div style="display:flex; gap:12px; margin:0.75rem 0;">'
            + "".join(cards) + "</div>")


def page_header(title: str, subtitle: str = "",
                live: bool = False) -> str:
    """Consistent page header."""
    badge = (
        '<span style="background:#DCFCE7; color:#14532D; font-size:0.72rem; '
        'font-weight:600; padding:2px 8px; border-radius:99px; margin-left:8px; '
        'vertical-align:middle;">Live</span>'
        if live else
        '<span style="background:#FEF9C3; color:#713F12; font-size:0.72rem; '
        'font-weight:600; padding:2px 8px; border-radius:99px; margin-left:8px; '
        'vertical-align:middle;">Historical</span>'
    )
    sub = (
        f'<p style="margin:0.3rem 0 0; font-size:0.875rem; opacity:0.55;">{subtitle}</p>'
        if subtitle else ""
    )
    return f"""
<div style="border-bottom:2px solid rgba(107,114,128,0.12);
            padding-bottom:0.9rem; margin-bottom:1.5rem;">
    <h1 style="margin:0; font-size:1.4rem; font-weight:700;
               letter-spacing:-0.02em; display:inline;">
        {title}
    </h1>{badge}
    {sub}
</div>"""


def disclaimer_footer() -> str:
    return """
<div style="text-align:center; font-size:0.72rem; opacity:0.4;
            border-top:1px solid rgba(107,114,128,0.15);
            padding-top:1rem; margin-top:2rem;">
    IRIS v1.0 — Intelligent Risk Integration System ·
    Policy Analysis Unit, CBK ·
    Simulated educational system — not an official CBK publication ·
    Lead Scientist: Stephen Munene
</div>"""

# ── Backward Compatibility Link ──────────────────────────────────────────────
# Map the layout file's old requests to your new semantic tokens!
COLOURS = {
    "primary": RISK["STABLE"]["accent"],    # Maps to Green (#16A34A)
    "secondary": RISK["MODERATE"]["accent"],# Maps to Amber (#D97706)
    "success": RISK["STABLE"]["bg"],        # Soft green background
    "danger": RISK["CRITICAL"]["accent"],   # Clear red accent
    "info": PLOT["interest_rate"]           # Safe blue tone
}

COLORS = COLOURS  # Supports both spellings just in case!