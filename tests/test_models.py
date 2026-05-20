# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Tests: Statistical Models
# ─────────────────────────────────────────────────────────────────────────────

import pytest
import pandas as pd
import numpy as np


def _sample_data(n=53):
    """Create realistic sample data for model tests."""
    np.random.seed(42)
    years = list(range(1971, 1971 + n))
    ir    = 6.0  + np.cumsum(np.random.randn(n) * 0.5)
    inf   = 9.0  + np.cumsum(np.random.randn(n) * 0.8)
    return pd.DataFrame({
        "year":          years,
        "interest_rate": ir,
        "inflation":     inf,
        "real_rate":     ir - inf,
        "above_target":  inf > 7.5,
    })


class TestStationarity:

    def test_adf_returns_dict(self):
        from models.stationarity import run_adf
        df = _sample_data()
        result = run_adf(df["interest_rate"], "test_ir")
        assert isinstance(result, dict)
        assert "statistic"     in result
        assert "p_value"       in result
        assert "is_stationary" in result
        assert "verdict"       in result

    def test_kpss_returns_dict(self):
        from models.stationarity import run_kpss
        df = _sample_data()
        result = run_kpss(df["inflation"], "test_inf")
        assert isinstance(result, dict)
        assert "statistic"     in result
        assert "is_stationary" in result

    def test_combined_stationarity(self):
        from models.stationarity import run_stationarity
        df = _sample_data()
        result = run_stationarity(df["interest_rate"], "interest_rate")
        assert "adf"         in result
        assert "kpss"        in result
        assert "combined"    in result
        assert "integration" in result

    def test_run_all_stationarity(self):
        from models.stationarity import run_all_stationarity
        df = _sample_data()
        results = run_all_stationarity(df)
        assert "interest_rate"      in results
        assert "inflation"          in results
        assert "interest_rate_diff" in results
        assert "inflation_diff"     in results

    def test_adf_on_stationary_series(self):
        """A white noise series should be stationary."""
        from models.stationarity import run_adf
        np.random.seed(0)
        wn = pd.Series(np.random.randn(100))
        result = run_adf(wn, "white_noise")
        assert result["is_stationary"]


class TestCorrelations:

    def test_correlations_run(self):
        from models.correlations import run_correlations
        df = _sample_data()
        result = run_correlations(df)
        assert "pearson_r"         in result
        assert "spearman_r"        in result
        assert "roll_corr"         in result
        assert "xcorr"             in result
        assert "fisher_slope"      in result
        assert "lead_lag_plain"    in result
        assert "pearson_plain"     in result

    def test_pearson_r_in_range(self):
        from models.correlations import run_correlations
        df = _sample_data()
        result = run_correlations(df)
        assert -1.0 <= result["pearson_r"] <= 1.0

    def test_spearman_r_in_range(self):
        from models.correlations import run_correlations
        df = _sample_data()
        result = run_correlations(df)
        assert -1.0 <= result["spearman_r"] <= 1.0

    def test_xcorr_length(self):
        from models.correlations import run_correlations
        df = _sample_data()
        result = run_correlations(df, max_lag=5)
        assert len(result["xcorr"]) == 11   # -5 to +5 = 11 values


class TestGARCH:

    def test_garch_runs(self):
        from models.garch import run_garch
        df = _sample_data()
        result = run_garch(df)
        assert "persistence"       in result
        assert "current_vol"       in result
        assert "historical_avg_vol" in result
        assert "garch_risk"        in result
        assert "cond_vol"          in result

    def test_persistence_in_range(self):
        from models.garch import run_garch
        df = _sample_data()
        result = run_garch(df)
        if "error" not in result:
            persistence = result["persistence"]
            assert 0 <= persistence <= 2.0   # Generous range for test data

    def test_garch_risk_label_valid(self):
        from models.garch import run_garch
        df = _sample_data()
        result = run_garch(df)
        if "error" not in result:
            assert result["garch_risk"] in ["LOW", "MODERATE", "ELEVATED", "HIGH", "UNKNOWN"]

    def test_insufficient_data_returns_error(self):
        from models.garch import run_garch
        df = _sample_data(n=5)
        result = run_garch(df)
        assert "error" in result


class TestFEVD:

    def test_fevd_runs(self):
        from models.fevd import run_fevd
        df = _sample_data()
        result = run_fevd(df, periods=6)
        assert "ir_share_lr"  in result
        assert "own_share_lr" in result
        assert "policy_power" in result

    def test_shares_sum_to_100(self):
        from models.fevd import run_fevd
        df = _sample_data()
        result = run_fevd(df, periods=6)
        if "error" not in result:
            total = result["ir_share_lr"] + result["own_share_lr"]
            assert abs(total - 100.0) < 1.0   # Should sum to ~100%

    def test_policy_power_label_valid(self):
        from models.fevd import run_fevd
        df = _sample_data()
        result = run_fevd(df, periods=6)
        if "error" not in result:
            assert result["policy_power"] in ["STRONG", "MODERATE", "LIMITED"]