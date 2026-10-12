"""
tests/test_cost_model.py
Phase 2 Failure Guard: Unit tests for dated cost schedule and calculations.
Verifies STT rates, round-trip charges, parametric scaling, and net <= gross rule.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import date
from src.costs.cost_model import (
    stt_rate,
    compute_round_trip_cost,
    apply_costs_to_returns,
    breakeven_cost_multiplier,
    STT_CUTOFF,
)


def test_stt_schedule_dated_transition():
    """Verify STT rate transitions correctly from 0.0125% to 0.0200% on Oct 1, 2024."""
    pre_rate = stt_rate(date(2024, 9, 30))
    post_rate = stt_rate(date(2024, 10, 1))
    
    assert pre_rate == 0.000125, f"Expected 0.0125% pre-Oct 2024, got {pre_rate}"
    assert post_rate == 0.000200, f"Expected 0.0200% post-Oct 2024, got {post_rate}"


def test_cost_multiplier_parametric_scaling():
    """Verify costs scale proportionally with cost_multiplier (0x, 0.5x, 1x, 1.5x)."""
    d = date(2023, 5, 15)
    notional = 1_000_000.0  # INR 10 Lakh
    
    c_zero = compute_round_trip_cost(notional, d, cost_multiplier=0.0)
    c_half = compute_round_trip_cost(notional, d, cost_multiplier=0.5)
    c_full = compute_round_trip_cost(notional, d, cost_multiplier=1.0)
    c_one_and_half = compute_round_trip_cost(notional, d, cost_multiplier=1.5)
    
    assert c_zero["total_inr"] == 0.0
    assert np.isclose(c_half["total_inr"] * 2, c_full["total_inr"])
    assert np.isclose(c_full["total_inr"] * 1.5, c_one_and_half["total_inr"])
    assert c_full["total_inr"] > 0, "Cost must be strictly positive"


def test_net_returns_never_exceed_gross():
    """Phase 2 Failure Guard: Net returns must always be strictly <= gross returns."""
    dates = pd.date_range("2023-01-01", periods=10, freq="B").date
    gross = pd.Series([0.01, -0.005, 0.02, 0.0, 0.015, -0.01, 0.005, 0.008, -0.002, 0.012])
    notionals = pd.Series([500_000.0] * 10)
    trade_dates = pd.Series(dates)
    adtv = pd.Series([80.0] * 10)
    
    net = apply_costs_to_returns(gross, notionals, trade_dates, adtv, cost_multiplier=1.0)
    
    # Net must be <= gross for every single observation
    assert (net <= gross).all(), "Phase 2 Guard Violation: Net returns exceed gross returns!"
    assert (gross - net > 0).all(), "Costs must be positive, reducing gross returns"


def test_breakeven_cost_solver():
    """Verify break-even solver returns a finite, positive multiplier."""
    gross_pa = 0.15  # 15% annual gross return
    avg_cost_bps = 8.0  # 8 bps per trade
    trades_pa = 100.0  # 100 trades a year
    
    be = breakeven_cost_multiplier(gross_pa, avg_cost_bps, trades_pa)
    assert np.isfinite(be)
    assert be > 0
    # At this multiplier, net return is exactly zero
    net_at_be = gross_pa - be * (avg_cost_bps * trades_pa) / 10_000
    assert np.isclose(net_at_be, 0.0)
