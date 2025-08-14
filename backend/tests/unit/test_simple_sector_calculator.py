"""
Unit tests for SectorCalculator weighted fallback behavior.

Validates that when computed weights are zero (price/volume zero),
the weighted mode returns the simple mean of changes_percentage.
"""

from __future__ import annotations

from services.simple_sector_calculator import SectorCalculator


def test_weighted_fallback_to_simple_when_zero_weights():
    calc = SectorCalculator(mode="weighted")
    stocks = [
        {"symbol": "A", "changes_percentage": 10.0, "current_price": 0.0, "volume": 0},
        {"symbol": "B", "changes_percentage": -5.0, "current_price": 0.0, "volume": 0},
        {"symbol": "C", "changes_percentage": 5.0, "current_price": 0.0, "volume": 0},
    ]
    expected = round((10.0 + -5.0 + 5.0) / 3.0, 4)
    result = calc.calculate_sector_performance(stocks)
    assert result == expected


def test_weighted_handles_empty_input():
    calc = SectorCalculator(mode="weighted")
    assert calc.calculate_sector_performance([]) == 0.0


def test_weighted_caps_95th_percentile_without_numpy(monkeypatch):
    # Force fallback path by making numpy import fail
    import builtins as _builtins

    real_import = _builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "numpy":
            raise ImportError("numpy not available for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(_builtins, "__import__", fake_import)

    calc = SectorCalculator(mode="weighted")
    # Extreme outlier weight on the negative mover; 95th-percentile cap should reduce to equal-ish weights
    stocks = [
        {"symbol": "A", "changes_percentage": 10.0, "current_price": 1.0, "volume": 1},
        {"symbol": "B", "changes_percentage": 10.0, "current_price": 1.0, "volume": 1},
        {"symbol": "C", "changes_percentage": -10.0, "current_price": 1.0, "volume": 1_000_000_000},
    ]
    expected_simple = round((10.0 + 10.0 + -10.0) / 3.0, 4)  # = 3.3333
    result = calc.calculate_sector_performance(stocks)
    assert result == expected_simple


