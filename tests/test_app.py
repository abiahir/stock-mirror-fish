"""
Unit tests for Stock Mirror Fish backend (app.py).
Run with: pytest tests/ -v
"""

import json
import time
import pytest
from freezegun import freeze_time

# ── Import only the pure utility symbols (no network, no yfinance at import time)
import importlib, sys, types

# Stub yfinance so import succeeds in CI without the full package installed
if "yfinance" not in sys.modules:
    yf_stub = types.ModuleType("yfinance")
    class _Ticker:
        def __init__(self, sym): pass
        fast_info = None
    yf_stub.Ticker = _Ticker
    sys.modules["yfinance"] = yf_stub

import app as smf  # noqa: E402


# ─────────────────────────────────────────────
#  Cache helpers
# ─────────────────────────────────────────────
class TestCache:
    def setup_method(self):
        smf.cache_clear()

    def test_miss_returns_none(self):
        assert smf.cache_get("missing") is None

    def test_set_then_get(self):
        smf.cache_set("k", {"x": 1})
        assert smf.cache_get("k") == {"x": 1}

    def test_expired_returns_none(self):
        with freeze_time("2026-01-01 12:00:00"):
            smf.cache_set("k2", "val")
        # Advance time well past TTL (300 s); entry must be treated as expired
        with freeze_time("2026-01-01 13:00:00"):
            assert smf.cache_get("k2") is None

    def test_clear_removes_all(self):
        smf.cache_set("a", 1)
        smf.cache_set("b", 2)
        smf.cache_clear()
        assert smf.cache_get("a") is None
        assert smf.cache_get("b") is None


# ─────────────────────────────────────────────
#  _sanitize_yahoo_str
# ─────────────────────────────────────────────
class TestSanitizeYahooStr:
    def test_none_returns_default(self):
        assert smf._sanitize_yahoo_str(None, 50) == ""
        assert smf._sanitize_yahoo_str(None, 50, "N/A") == "N/A"

    def test_truncates_to_max_len(self):
        long = "A" * 200
        result = smf._sanitize_yahoo_str(long, 10)
        assert len(result) <= 10

    def test_strips_control_chars(self):
        result = smf._sanitize_yahoo_str("hello\x00world\x01", 50)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "hello" in result

    def test_collapses_whitespace(self):
        result = smf._sanitize_yahoo_str("  hello   world  ", 50)
        assert result == "hello world"

    def test_non_string_coerced(self):
        result = smf._sanitize_yahoo_str(42, 50)
        assert result == "42"


# ─────────────────────────────────────────────
#  _parse_yahoo_search_json
# ─────────────────────────────────────────────
class TestParseYahooSearchJson:
    def _enc(self, obj):
        return json.dumps(obj).encode()

    def test_valid_with_quotes(self):
        raw = self._enc({"quotes": [{"symbol": "AAPL"}], "news": []})
        data = smf._parse_yahoo_search_json(raw)
        assert data["quotes"][0]["symbol"] == "AAPL"

    def test_empty_bytes_raises(self):
        with pytest.raises(ValueError, match="empty"):
            smf._parse_yahoo_search_json(b"")

    def test_non_dict_raises(self):
        with pytest.raises(ValueError, match="JSON object"):
            smf._parse_yahoo_search_json(self._enc([1, 2, 3]))

    def test_quotes_null_is_ok(self):
        raw = self._enc({"quotes": None})
        data = smf._parse_yahoo_search_json(raw)
        assert data["quotes"] is None

    def test_quotes_not_list_raises(self):
        with pytest.raises(ValueError, match="array"):
            smf._parse_yahoo_search_json(self._enc({"quotes": "bad"}))


# ─────────────────────────────────────────────
#  Metrics
# ─────────────────────────────────────────────
class TestMetrics:
    def setup_method(self):
        with smf._metrics_lock:
            smf._metrics.clear()

    def test_increment_and_snapshot(self):
        smf._metric_inc("test_key")
        smf._metric_inc("test_key")
        snap = smf.metrics_snapshot()
        assert snap["test_key"] == 2

    def test_snapshot_is_copy(self):
        smf._metric_inc("k")
        snap = smf.metrics_snapshot()
        snap["k"] = 999
        assert smf.metrics_snapshot()["k"] == 1


# ─────────────────────────────────────────────
#  Market session logic (static/deterministic checks)
# ─────────────────────────────────────────────
class TestIsMarketOpen:
    def test_returns_bool(self):
        result = smf.is_market_open()
        assert isinstance(result, bool)

    def test_cache_staleness_threshold(self):
        """Within the 30 s window, a second call reuses the cached result."""
        with freeze_time("2026-01-01 12:00:00"):
            smf.is_market_open()  # prime the cache
            original_checked = smf._market_status["checked"]
        # 15 s later — still inside the 30 s staleness window
        with freeze_time("2026-01-01 12:00:15"):
            smf.is_market_open()
            assert smf._market_status["checked"] == original_checked
