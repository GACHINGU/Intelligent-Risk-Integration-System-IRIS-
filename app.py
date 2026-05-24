# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Intelligent Risk Integration System
# Main Streamlit Application Entry Point
# Run with: streamlit run app.py
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
st.set_page_config(
    page_title="IRIS — Intelligent Risk Integration System",
    page_icon="🇰🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
from datetime import datetime
from dashboard.style.theme import GLOBAL_CSS, RISK

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Internal modules ───────────────────────────────────────────────────────────
from data.ingestion.trading_economics import fetch_all_kenya_indicators
from data.ingestion.cache             import (save_to_cache, load_from_cache,
                                               is_cache_valid, get_cache_age_minutes)
from data.pipeline.cleaner            import clean_all
from data.pipeline.merger             import merge_with_historical
from data.pipeline.features           import build_features
from models.model_runner              import run_all_models
from risk.score_builder               import build_iris_score
from risk.regime_classifier           import classify
from risk.signal_engine               import generate_signals
from intelligence.memo_generator      import generate_all_memos
from scheduler.alerts                 import (check_and_generate_alerts,
                                               get_alert_summary, get_unread_alerts)
from config.settings                  import APP_VERSION

# ── Page imports ───────────────────────────────────────────────────────────────
from dashboard.pages import (
    page_home, page_live_data, page_risk_gauge,
    page_models, page_correlations, page_statistics,
    page_memorandum, page_history,
)
from dashboard.pages import page_simulator, page_fisher


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING (cached 1 hour)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_iris_system():
    # ── Fetch ──────────────────────────────────────────────────────────────────
    if is_cache_valid():
        live = load_from_cache()
    else:
        live = fetch_all_kenya_indicators()
        if live["success"]:
            save_to_cache(live)
        else:
            cached = load_from_cache()
            if cached:
                live = cached

    # ── Pipeline ───────────────────────────────────────────────────────────────
    cleaned  = clean_all(live)
    merged   = merge_with_historical(cleaned)
    features = build_features(merged["combined"])

    # ── Latest readings ────────────────────────────────────────────────────────
    latest = merged.get("latest", {})
    if not latest:
        last_row = features.iloc[-1]
        latest = {
            "inflation":     {"value": float(last_row["inflation"]),     "date": str(int(last_row["year"]))},
            "interest_rate": {"value": float(last_row["interest_rate"]), "date": str(int(last_row["year"]))},
        }
    features_tail = features.iloc[-1].to_dict()

    # ── Models ─────────────────────────────────────────────────────────────────
    model_results = run_all_models(features)

    # ── Risk engine ────────────────────────────────────────────────────────────
    iris_score_result = build_iris_score(model_results, latest, features_tail)
    classification    = classify(iris_score_result, model_results, latest)
    signals           = generate_signals(classification, model_results, latest, iris_score_result)

    # ── Intelligence ───────────────────────────────────────────────────────────
    memos = generate_all_memos(
        model_results, latest, iris_score_result,
        classification, signals, features_tail,
    )

    # ── Alerts ─────────────────────────────────────────────────────────────────
    check_and_generate_alerts(iris_score_result, classification, model_results, latest)
    alert_summary = get_alert_summary()

    return {
        "features":        features,
        "merged":          merged,
        "model_results":   model_results,
        "latest":          latest,
        "features_tail":   features_tail,
        "iris_score":      iris_score_result,
        "classification":  classification,
        "signals":         signals,
        "memos":           memos,
        "alert_summary":   alert_summary,
        "live_available":  merged.get("live_available", False),
        "loaded_at":       datetime.now(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar(iris: dict) -> str:
    with st.sidebar:
        # ── Brand mark ────────────────────────────────────────────────────────
        st.markdown("""
        <div style="padding:1.25rem 0 0.5rem; text-align:center;">
            <div style="font-size:1.8rem; line-height:1;">🇰🇪</div>
            <div style="font-size:1rem; font-weight:700; color:#F1F5F9;
                        margin-top:0.3rem; letter-spacing:0.05em;">IRIS</div>
            <div style="font-size:0.7rem; color:#64748B; margin-top:0.1rem;">
                Intelligent Risk Integration System
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:0.5rem 0">', unsafe_allow_html=True)

        # ── IRIS Score ────────────────────────────────────────────────────────
        score  = iris["iris_score"]["iris_score"]
        regime = iris["classification"]["regime"]
        r      = RISK.get(regime, RISK["MODERATE"])

        # Score block — dark bg so coloured text is readable
        score_text_col = {
            "STABLE": "#4ADE80", "MODERATE": "#FCD34D",
            "DANGER": "#FB923C", "CRITICAL": "#F87171",
        }.get(regime, "#FCD34D")

        st.markdown(f"""
        <div style="margin:0.5rem 0 0.75rem; padding:0.9rem 0.75rem;
                    background:rgba(255,255,255,0.04);
                    border:1px solid rgba(255,255,255,0.08);
                    border-radius:10px; text-align:center;">
            <div style="font-size:2.4rem; font-weight:700; color:{score_text_col};
                        line-height:1; letter-spacing:-0.03em;">
                {score:.0f}
            </div>
            <div style="font-size:0.7rem; color:#64748B; margin:0.15rem 0 0.4rem;">
                / 100 · risk score
            </div>
            <div style="font-size:0.85rem; font-weight:600; color:{score_text_col};">
                {r['emoji']} {regime}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Alert badge ───────────────────────────────────────────────────────
        alert_sum = iris.get("alert_summary", {})
        n_crit    = alert_sum.get("critical_count", 0)
        n_alert   = alert_sum.get("alert_count",    0)
        n_unread  = alert_sum.get("unread_count",   0)
        if n_unread > 0:
            a_col = "#F87171" if n_crit > 0 else "#FB923C"
            st.markdown(f"""
            <div style="background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.25);
                        border-radius:8px; padding:0.4rem 0.75rem; margin-bottom:0.5rem;
                        font-size:0.75rem; color:{a_col}; font-weight:500; text-align:center;">
                🔔 {n_unread} alert{"s" if n_unread > 1 else ""}
                &nbsp;·&nbsp; {n_crit} critical &nbsp;·&nbsp; {n_alert} alerts
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:0.25rem 0 0.5rem">', unsafe_allow_html=True)

        # ── Navigation ────────────────────────────────────────────────────────
        st.markdown('<p style="font-size:0.68rem; color:#475569; font-weight:600; '
                    'text-transform:uppercase; letter-spacing:0.08em; '
                    'margin:0 0 0.3rem; padding:0 0.1rem;">Navigation</p>',
                    unsafe_allow_html=True)

        page = st.radio(
            label="",
            options=[
                "🏠  Home",
                "📡  Live Data",
                "🎯  Risk Gauge",
                "🤖  Models",
                "📊  Correlations",
                "📈  Statistics",
                "📋  Memorandum",
                "📚  History",
                "🔬  Simulator",
                "📐  Fisher Tracker",
            ],
            label_visibility="collapsed",
        )

        st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:0.5rem 0">', unsafe_allow_html=True)

        # ── Status ────────────────────────────────────────────────────────────
        live_ok   = iris.get("live_available", False)
        loaded_at = iris.get("loaded_at", datetime.now())
        models_ok = iris["model_results"].get("models_ok", "?")
        models_n  = iris["model_results"].get("models_total", "?")

        status_dot  = "🟢" if live_ok else "🟡"
        status_text = "Live data" if live_ok else "Historical data"

        st.markdown(f"""
        <div style="font-size:0.73rem; color:#475569; line-height:1.8;">
            <div>{status_dot} {status_text}</div>
            <div>Updated {loaded_at.strftime('%H:%M:%S')}</div>
            <div>Models: {models_ok}/{models_n} passing</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="margin-top:0.6rem;"></div>', unsafe_allow_html=True)
        if st.button("↺ Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    return page


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    with st.spinner("🔄 IRIS is loading — running models and building risk score..."):
        iris = load_iris_system()

    page = render_sidebar(iris)

    routes = {
        "Home":           page_home.render,
        "Live Data":      page_live_data.render,
        "Risk Gauge":     page_risk_gauge.render,
        "Models":         page_models.render,
        "Correlations":   page_correlations.render,
        "Statistics":     page_statistics.render,
        "Memorandum":     page_memorandum.render,
        "History":        page_history.render,
        "Simulator":      page_simulator.render,
        "Fisher Tracker": page_fisher.render,
    }

    for key, fn in routes.items():
        if key in page:
            fn(iris)
            break


if __name__ == "__main__":
    main()