# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Tests: Intelligence Layer (Narrative + Memos + Exporter)
# ─────────────────────────────────────────────────────────────────────────────

import pytest


def _mock_context():
    """Build a minimal mock context for memo tests."""
    from intelligence.narrative_engine import build_full_narrative

    iris_score = {
        "iris_score":         45.0,
        "regime_label":       "MODERATE",
        "regime_emoji":       "🟡",
        "regime_colour":      "#C5A028",
        "urgency":            "MEDIUM",
        "dominant_driver":    "inflation_level",
        "dominant_driver_label": "Elevated inflation level",
        "components":         {"inflation_level": 45},
    }
    classification = {
        "regime":          "MODERATE",
        "urgency":         "MEDIUM",
        "description":     "Moderate risk environment.",
        "plain_english":   "Prices are rising a bit faster than ideal.",
        "policy_signal":   "WATCH — consider gradual tightening.",
        "early_warnings":  [],
        "conditions":      [],
        "dominant_driver": "Elevated inflation level",
        "headline":        "🟡 IRIS Risk Score: 45.0/100 — MODERATE",
    }
    signals = {
        "signals":         [{"type": "RATE_ACTION", "action": "WATCH AND PREPARE",
                             "detail": "Hold but prepare.", "priority": 2}],
        "rate_signal":     "WATCH AND PREPARE",
        "priority_action": {"type": "RATE_ACTION", "action": "WATCH AND PREPARE",
                            "detail": "Hold but prepare.", "priority": 2},
    }
    latest = {
        "inflation":     {"value": 8.5,  "date": "2023"},
        "interest_rate": {"value": 7.0,  "date": "2023"},
    }
    features_tail = {"real_rate": -1.5, "inflation": 8.5, "interest_rate": 7.0}
    model_results = {}

    from datetime import datetime
    narrative_p = build_full_narrative(model_results, latest, iris_score, features_tail, "POLICY")
    narrative_t = build_full_narrative(model_results, latest, iris_score, features_tail, "TECHNICAL")
    narrative_pl = build_full_narrative(model_results, latest, iris_score, features_tail, "PLAIN")

    return {
        "iris_score":          iris_score,
        "classification":      classification,
        "signals":             signals,
        "model_results":       model_results,
        "latest":              latest,
        "features_tail":       features_tail,
        "generated_at":        datetime.now(),
        "policy_narrative":    narrative_p,
        "technical_narrative": narrative_t,
        "plain_narrative":     narrative_pl,
    }


class TestNarrativeEngine:

    def test_situation_narrative_all_levels(self):
        from intelligence.narrative_engine import narrate_current_situation
        latest = {"inflation": {"value": 9.0}, "interest_rate": {"value": 7.0}}
        iris   = {"iris_score": 50, "regime_label": "MODERATE",
                  "regime_emoji": "🟡", "dominant_driver_label": "test"}
        features_tail = {"real_rate": -2.0}

        for level in ["TECHNICAL", "POLICY", "PLAIN"]:
            text = narrate_current_situation(latest, features_tail, iris, level)
            assert isinstance(text, str)
            assert len(text) > 50

    def test_full_narrative_has_all_sections(self):
        from intelligence.narrative_engine import build_full_narrative
        latest = {"inflation": {"value": 8.0}, "interest_rate": {"value": 7.0}}
        iris   = {"iris_score": 45, "regime_label": "MODERATE",
                  "regime_emoji": "🟡", "dominant_driver_label": "test"}
        features_tail = {"real_rate": -1.0}

        result = build_full_narrative({}, latest, iris, features_tail, "POLICY")
        for key in ["situation", "vecm", "irf", "fevd", "garch", "regime", "executive_summary"]:
            assert key in result
            assert isinstance(result[key], str)

    def test_safe_format_handles_none(self):
        from intelligence.narrative_engine import _safe
        assert _safe(None)       == "N/A"
        assert _safe(3.14, ".1f") == "3.1"
        assert _safe("bad")      == "N/A"


class TestGovernorMemo:

    def test_governor_memo_builds(self):
        from intelligence.templates.governor_memo import build_governor_memo
        context = _mock_context()
        memo    = build_governor_memo(context)
        assert memo["type"]      == "GOVERNOR_MEMO"
        assert "sections"        in memo
        assert len(memo["sections"]) > 0
        assert "full_text"       in memo
        assert "addressee"       in memo

    def test_governor_memo_has_required_sections(self):
        from intelligence.templates.governor_memo import build_governor_memo
        memo = build_governor_memo(_mock_context())
        titles = [s["title"] for s in memo["sections"]]
        assert any("RISK" in t.upper()          for t in titles)
        assert any("RECOMMEND" in t.upper()     for t in titles)


class TestMPCMemo:

    def test_mpc_memo_builds(self):
        from intelligence.templates.mpc_memo import build_mpc_memo
        memo = build_mpc_memo(_mock_context())
        assert memo["type"]      == "MPC_MEMO"
        assert "rate_signal"     in memo
        assert "sections"        in memo
        assert len(memo["sections"]) > 0

    def test_mpc_memo_has_rate_signal(self):
        from intelligence.templates.mpc_memo import build_mpc_memo
        memo = build_mpc_memo(_mock_context())
        assert memo["rate_signal"] in [
            "HOLD", "WATCH AND PREPARE", "TIGHTEN", "EMERGENCY TIGHTENING"
        ]


class TestWananchiBrief:

    def test_wananchi_brief_builds(self):
        from intelligence.templates.wananchi_brief import build_wananchi_brief
        brief = build_wananchi_brief(_mock_context())
        assert brief["type"]           == "WANANCHI_BRIEF"
        assert "status_swahili"        in brief
        assert "status_english"        in brief
        assert "sections"              in brief
        assert len(brief["sections"])  > 0

    def test_wananchi_uses_plain_language(self):
        from intelligence.templates.wananchi_brief import build_wananchi_brief
        brief = build_wananchi_brief(_mock_context())
        full  = brief["full_text"].lower()
        # Should contain relatable Kenyan examples
        assert any(word in full for word in ["unga", "kenya", "savings", "cbk", "inflation"])


class TestExporter:

    def test_pdf_export_returns_bytes(self):
        from intelligence.templates.governor_memo import build_governor_memo
        from utils.exporter import export_memo_to_pdf
        memo  = build_governor_memo(_mock_context())
        pdf   = export_memo_to_pdf(memo)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000   # A real PDF is never tiny
        assert pdf[:4] == b"%PDF"  # PDF magic bytes

    def test_pdf_filename_format(self):
        from utils.exporter import get_pdf_download_name
        name = get_pdf_download_name("GOVERNOR_MEMO")
        assert name.endswith(".pdf")
        assert "Governor" in name

    def test_all_memo_types_export(self):
        from intelligence.templates.mpc_memo       import build_mpc_memo
        from intelligence.templates.wananchi_brief import build_wananchi_brief
        from utils.exporter import export_memo_to_pdf
        ctx     = _mock_context()
        for builder in [build_mpc_memo, build_wananchi_brief]:
            memo = builder(ctx)
            pdf  = export_memo_to_pdf(memo)
            assert isinstance(pdf, bytes)
            assert pdf[:4] == b"%PDF"