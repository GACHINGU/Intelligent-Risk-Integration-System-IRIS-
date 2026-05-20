# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Tests: Risk Engine
# ─────────────────────────────────────────────────────────────────────────────

import pytest


class TestScoreBuilder:

    def _mock_latest(self, inf=8.0, ir=7.0):
        return {
            "inflation":     {"value": inf, "date": "2023"},
            "interest_rate": {"value": ir,  "date": "2023"},
        }

    def test_score_in_range(self):
        from risk.score_builder import build_iris_score
        model_results = {}
        latest        = self._mock_latest()
        features_tail = {"real_rate": -1.0, "inflation": 8.0, "interest_rate": 7.0}
        result        = build_iris_score(model_results, latest, features_tail)
        assert 0 <= result["iris_score"] <= 100

    def test_high_inflation_increases_score(self):
        from risk.score_builder import build_iris_score
        low_inf  = build_iris_score({}, self._mock_latest(inf=5.0,  ir=8.0), {"real_rate": 3.0})
        high_inf = build_iris_score({}, self._mock_latest(inf=20.0, ir=8.0), {"real_rate": -12.0})
        assert high_inf["iris_score"] > low_inf["iris_score"]

    def test_regime_label_correct(self):
        from risk.score_builder import build_iris_score
        result = build_iris_score({}, self._mock_latest(inf=5.0, ir=8.0), {"real_rate": 3.0})
        assert result["regime_label"] in ["STABLE", "MODERATE", "DANGER", "CRITICAL"]

    def test_dominant_driver_present(self):
        from risk.score_builder import build_iris_score
        result = build_iris_score({}, self._mock_latest(), {"real_rate": -1.0})
        assert "dominant_driver"       in result
        assert "dominant_driver_label" in result

    def test_components_all_present(self):
        from risk.score_builder import build_iris_score
        result = build_iris_score({}, self._mock_latest(), {"real_rate": 0.0})
        expected_keys = [
            "inflation_level", "real_rate", "garch_vol",
            "regime_prob", "vecm_deviation", "correlation", "fevd_supply"
        ]
        for key in expected_keys:
            assert key in result["components"]

    def test_component_scores_in_range(self):
        from risk.score_builder import build_iris_score
        result = build_iris_score({}, self._mock_latest(), {"real_rate": 0.0})
        for key, val in result["components"].items():
            assert 0 <= val <= 100, f"Component {key} = {val} is out of range"


class TestRegimeClassifier:

    def _mock_iris_score(self, score=40.0):
        colours = {
            "STABLE": "#006400", "MODERATE": "#C5A028",
            "DANGER": "#E65100", "CRITICAL": "#8B0000"
        }
        if score <= 25:   regime = "STABLE"
        elif score <= 50: regime = "MODERATE"
        elif score <= 75: regime = "DANGER"
        else:             regime = "CRITICAL"
        return {
            "iris_score":         score,
            "regime_label":       regime,
            "regime_emoji":       "🟡",
            "regime_colour":      colours[regime],
            "urgency":            "MEDIUM",
            "dominant_driver":    "inflation_level",
            "dominant_driver_label": "Elevated inflation level",
            "components":         {"inflation_level": 50},
        }

    def test_classify_returns_regime(self):
        from risk.regime_classifier import classify
        result = classify(self._mock_iris_score(40), {}, {"inflation": {"value": 8.0}})
        assert "regime"        in result
        assert "urgency"       in result
        assert "early_warnings" in result
        assert "headline"      in result

    def test_stable_score_gives_stable_regime(self):
        from risk.regime_classifier import classify
        result = classify(self._mock_iris_score(15), {}, {"inflation": {"value": 5.0}})
        assert result["regime"] == "STABLE"

    def test_critical_score_gives_critical_regime(self):
        from risk.regime_classifier import classify
        result = classify(
            self._mock_iris_score(85),
            {"garch": {"vol_ratio": 3.0, "persistence": 0.99}},
            {"inflation": {"value": 30.0}, "interest_rate": {"value": 5.0}},
        )
        assert result["regime"] == "CRITICAL"

    def test_high_inflation_triggers_warning(self):
        from risk.regime_classifier import classify
        result = classify(
            self._mock_iris_score(60),
            {},
            {"inflation": {"value": 20.0}, "interest_rate": {"value": 5.0}},
        )
        flags = [w["flag"] for w in result["early_warnings"]]
        assert any("INFLATION" in f for f in flags)


class TestSignalEngine:

    def _mock_classification(self, regime="DANGER", score=60):
        return {
            "iris_score":      score,
            "regime":          regime,
            "urgency":         "HIGH",
            "early_warnings":  [],
        }

    def test_signals_generated(self):
        from risk.signal_engine import generate_signals
        clf    = self._mock_classification()
        result = generate_signals(clf, {}, {"inflation": {"value": 12.0}}, {})
        assert "signals"         in result
        assert "rate_signal"     in result
        assert "priority_action" in result
        assert len(result["signals"]) > 0

    def test_critical_regime_triggers_emergency(self):
        from risk.signal_engine import generate_signals
        clf    = self._mock_classification("CRITICAL", 85)
        result = generate_signals(clf, {}, {"inflation": {"value": 25.0}}, {})
        assert "EMERGENCY" in result["rate_signal"] or "TIGHTEN" in result["rate_signal"]

    def test_stable_regime_triggers_hold(self):
        from risk.signal_engine import generate_signals
        clf    = self._mock_classification("STABLE", 15)
        result = generate_signals(clf, {}, {"inflation": {"value": 5.0}}, {})
        assert result["rate_signal"] == "HOLD"

    def test_all_signal_types_have_required_keys(self):
        from risk.signal_engine import generate_signals
        clf    = self._mock_classification("MODERATE", 40)
        result = generate_signals(clf, {}, {"inflation": {"value": 8.5}}, {})
        for sig in result["signals"]:
            assert "type"     in sig
            assert "action"   in sig
            assert "detail"   in sig
            assert "priority" in sig