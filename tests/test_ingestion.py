# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Tests: Data Ingestion
# Run with: python -m pytest tests/ -v
# ─────────────────────────────────────────────────────────────────────────────

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from data.ingestion.validator import validate_dataframe, validate_all, ValidationResult
from data.ingestion.cache import save_to_cache, load_from_cache, is_cache_valid
from datetime import datetime


class TestValidator:

    def _sample_df(self, n=30):
        """Create a clean sample DataFrame."""
        return pd.DataFrame({
            "date":  pd.date_range("2000-01-01", periods=n, freq="YS"),
            "value": [5.0 + i * 0.1 for i in range(n)],
        })

    def test_valid_dataframe_passes(self):
        df = self._sample_df()
        result = validate_dataframe(df, "inflation")
        assert result.passed is True
        assert len(result.errors) == 0

    def test_empty_dataframe_fails(self):
        result = validate_dataframe(pd.DataFrame(), "inflation")
        assert result.passed is False
        assert len(result.errors) > 0

    def test_none_dataframe_fails(self):
        result = validate_dataframe(None, "inflation")
        assert result.passed is False

    def test_missing_value_column_fails(self):
        df = pd.DataFrame({"date": pd.date_range("2000", periods=5, freq="YS")})
        result = validate_dataframe(df, "inflation")
        assert result.passed is False

    def test_insufficient_observations_fails(self):
        df = self._sample_df(n=5)   # Below MIN_OBSERVATIONS of 20
        result = validate_dataframe(df, "inflation")
        assert result.passed is False

    def test_out_of_range_values_generate_warning(self):
        df = self._sample_df()
        df.loc[0, "value"] = 999.0   # Above plausible max
        result = validate_dataframe(df, "inflation")
        # Should pass but with a warning
        assert len(result.warnings) > 0

    def test_validate_all_empty_data(self):
        live = {"inflation": pd.DataFrame(), "interest_rate": pd.DataFrame()}
        results = validate_all(live)
        assert results["overall_passed"] is False

    def test_validation_result_repr(self):
        r = ValidationResult(True, ["w1"], [])
        assert "PASSED" in repr(r)
        r2 = ValidationResult(False, [], ["e1"])
        assert "FAILED" in repr(r2)


class TestCache:

    def test_save_and_load_cache(self, tmp_path, monkeypatch):
        """Test that data can be saved and loaded from cache."""
        import data.ingestion.cache as cache_module
        monkeypatch.setattr(cache_module, "CACHE_PATH", str(tmp_path))
        monkeypatch.setattr(cache_module, "CACHE_FILES", {
            "inflation":     str(tmp_path / "inflation.csv"),
            "interest_rate": str(tmp_path / "interest_rate.csv"),
            "metadata":      str(tmp_path / "metadata.json"),
        })

        data = {
            "inflation":     pd.DataFrame({"date": pd.date_range("2000", periods=3, freq="YS"), "value": [5.0, 6.0, 7.0]}),
            "interest_rate": pd.DataFrame({"date": pd.date_range("2000", periods=3, freq="YS"), "value": [8.0, 9.0, 10.0]}),
            "latest":        {"inflation": {"value": 7.0, "date": datetime(2002, 1, 1)},
                               "interest_rate": {"value": 10.0, "date": datetime(2002, 1, 1)}},
            "fetch_time":    datetime.now(),
            "success":       True,
        }

        save_result = cache_module.save_to_cache(data)
        assert save_result is True

        loaded = cache_module.load_from_cache()
        assert loaded is not None
        assert not loaded["inflation"].empty
        assert not loaded["interest_rate"].empty