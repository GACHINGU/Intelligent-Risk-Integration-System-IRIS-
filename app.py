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
from dashboard.style.theme import GLOBAL_CSS

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
        # Logo
        st.markdown(f"""
        <div style='text-align:center; padding:1rem 0;'>
            <div style='font-size:2rem;'>🇰🇪</div>
            <div style='font-size:1.1rem; font-weight:bold; color:#C5A028;'>IRIS</div>
            <div style='font-size:0.72rem; color:#AAAAAA;'>Intelligent Risk Integration System</div>
            <div style='font-size:0.62rem; color:#888888;'>v{APP_VERSION}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # IRIS Score badge
        score  = iris["iris_score"]["iris_score"]
        emoji  = iris["classification"]["regime_emoji"]
        regime = iris["classification"]["regime"]
        colour = iris["iris_score"]["regime_colour"]

        st.markdown(f"""
        <div style='text-align:center; background:{colour}22; border:2px solid {colour};
                    border-radius:10px; padding:1rem; margin:0.5rem 0;'>
            <div style='font-size:2.4rem; font-weight:bold; color:{colour};'>{score:.0f}</div>
            <div style='font-size:0.82rem; color:{colour}; font-weight:bold;'>
                {emoji} {regime}
            </div>
            <div style='font-size:0.65rem; color:#888;'>IRIS Risk Score / 100</div>
        </div>
        """, unsafe_allow_html=True)

        # Alert badge
        alert_sum = iris.get("alert_summary", {})
        n_crit    = alert_sum.get("critical_count", 0)
        n_alert   = alert_sum.get("alert_count",    0)
        n_unread  = alert_sum.get("unread_count",   0)
        if n_unread > 0:
            badge_col = "#8B0000" if n_crit > 0 else "#E65100"
            st.markdown(f"""
            <div style='background:{badge_col}18; border:1px solid {badge_col};
                        border-radius:6px; padding:0.4rem 0.8rem; margin:0.3rem 0;
                        text-align:center; font-size:0.75rem; color:{badge_col};
                        font-weight:bold;'>
                🔔 {n_unread} unread alert(s) ·
                {n_crit} critical · {n_alert} alerts
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation
        st.markdown(
            "<div style='font-size:0.78rem; color:#C5A028; font-weight:bold; "
            "letter-spacing:1px;'>NAVIGATION</div>",
            unsafe_allow_html=True,
        )

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

        st.markdown("---")

        # Data status
        live_ok   = iris.get("live_available", False)
        cache_age = get_cache_age_minutes()
        loaded_at = iris.get("loaded_at", datetime.now())

        st.markdown(f"""
        <div style='font-size:0.72rem; color:#AAAAAA;'>
            <div>{'🟢 Live data' if live_ok else '🟡 Historical data'}</div>
            <div>Last run: {loaded_at.strftime('%H:%M:%S')}</div>
            {'<div>Cache age: ' + str(cache_age) + ' min</div>' if cache_age else ''}
            <div>Models: {iris["model_results"].get("models_ok","?")}/{iris["model_results"].get("models_total","?")} OK</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        if st.button("🔄 Refresh Data", use_container_width=True):
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