# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Layout Constants
# Page layout helpers and shared structural elements.
# ─────────────────────────────────────────────────────────────────────────────

from dashboard.style.theme import COLOURS


def page_header(title: str, subtitle: str = "", live: bool = False) -> str:
    """Render a consistent page header."""
    live_badge = (
        '<span style="background:#006400; color:white; font-size:0.7rem; '
        'padding:2px 8px; border-radius:10px; margin-left:8px;">🟢 LIVE</span>'
        if live else
        '<span style="background:#C5A028; color:white; font-size:0.7rem; '
        'padding:2px 8px; border-radius:10px; margin-left:8px;">🟡 HISTORICAL</span>'
    )
    sub = f"<p style='color:#777; font-size:0.88rem; margin:0.2rem 0 0 0;'>{subtitle}</p>" if subtitle else ""
    return f"""
    <div style='border-bottom:2px solid #006400; padding-bottom:0.8rem; margin-bottom:1.2rem;'>
        <h2 style='margin:0; color:#003300;'>{title}{live_badge}</h2>
        {sub}
    </div>
    """


def disclaimer_footer() -> str:
    """Render the standard IRIS disclaimer footer."""
    return """
    <div style='text-align:center; font-size:0.7rem; color:#AAAAAA;
                border-top:1px solid #EEEEEE; padding-top:0.8rem; margin-top:1.5rem;'>
        IRIS v1.0 — Intelligent Risk Integration System ·
        Policy Analysis Unit, Central Bank of Kenya ·
        Simulated Educational System · Not an official CBK publication ·
        Lead Scientist: Stephen Munene
    </div>
    """


def info_callout(text: str, icon: str = "ℹ️") -> str:
    """Render a plain info callout box."""
    return f"""
    <div style='background:#E8F5E9; border-left:4px solid #006400;
                padding:0.7rem 1rem; border-radius:6px; margin:0.5rem 0;
                font-size:0.88rem; color:#333; line-height:1.5;'>
        {icon} {text}
    </div>
    """


def section_divider(label: str = "") -> str:
    """Render a section divider with optional label."""
    if label:
        return f"""
        <div style='display:flex; align-items:center; margin:1rem 0;'>
            <div style='flex:1; height:1px; background:#DDDDDD;'></div>
            <div style='padding:0 0.8rem; font-size:0.78rem; color:#888;
                        font-weight:bold; text-transform:uppercase; letter-spacing:1px;'>
                {label}
            </div>
            <div style='flex:1; height:1px; background:#DDDDDD;'></div>
        </div>
        """
    return "<hr style='border:none; border-top:1px solid #EEEEEE; margin:1rem 0;'>"