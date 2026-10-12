"""
tests/test_adjustments.py
Phase 1 Failure Guard #3: Unit-tests for corporate action adjustments.
Verifies bonus, split, and total-return factor adjustments on known events.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import date
from src.data.adjust import apply_adjustments, compute_adjustment_factors, unit_test_adjustments, KNOWN_EVENTS


def test_bonus_1_to_1_halving():
    """Verify that a 1:1 bonus results in a 0.5 adjustment factor for dates before ex-date."""
    dates = pd.date_range("2018-06-01", "2018-06-20", freq="B")
    df = pd.DataFrame({
        "symbol": "INFY",
        "trade_date": dates,
        "close": [2000.0 if d < pd.Timestamp("2018-06-14") else 1000.0 for d in dates]
    })
    
    ca = pd.DataFrame([{
        "symbol": "INFY",
        "ex_date": pd.Timestamp("2018-06-14"),
        "purpose": "BONUS ISSUE",
        "ratio": "1:1"
    }])
    
    factors = compute_adjustment_factors(ca, ["INFY"])
    assert len(factors) == 1
    assert factors.iloc[0]["factor"] == 0.5
    
    adj_df = apply_adjustments(df, factors)
    
    # Prices before bonus should now be 2000 * 0.5 = 1000
    before_bonus = adj_df[adj_df["trade_date"] < "2018-06-14"]["adj_close"]
    assert np.allclose(before_bonus, 1000.0)
    
    # Prices on or after bonus remain 1000
    after_bonus = adj_df[adj_df["trade_date"] >= "2018-06-14"]["adj_close"]
    assert np.allclose(after_bonus, 1000.0)


def test_split_2_to_1():
    """Verify that a 2:1 stock split divides pre-split prices by 2."""
    dates = pd.date_range("2021-01-01", "2021-01-10", freq="B")
    df = pd.DataFrame({
        "symbol": "TEST",
        "trade_date": dates,
        "close": [500.0 if d < pd.Timestamp("2021-01-06") else 250.0 for d in dates]
    })
    
    ca = pd.DataFrame([{
        "symbol": "TEST",
        "ex_date": pd.Timestamp("2021-01-06"),
        "purpose": "STOCK SPLIT / SUB-DIVISION",
        "ratio": "2:1"
    }])
    
    factors = compute_adjustment_factors(ca, ["TEST"])
    assert len(factors) == 1
    assert factors.iloc[0]["factor"] == 0.5
    
    adj_df = apply_adjustments(df, factors)
    before_split = adj_df[adj_df["trade_date"] < "2021-01-06"]["adj_close"]
    assert np.allclose(before_split, 250.0)


def test_unit_test_adjustments_function():
    """Verify the Phase 1 Failure Guard #3 validation function passes with compliant data."""
    dates = pd.date_range("2018-06-01", "2018-06-25", freq="B")
    df = pd.DataFrame({
        "symbol": "INFY",
        "trade_date": dates,
        "close": [2400.0 if d < pd.Timestamp("2018-06-14") else 1200.0 for d in dates]
    })
    ca = pd.DataFrame([{
        "symbol": "INFY",
        "ex_date": pd.Timestamp("2018-06-14"),
        "purpose": "BONUS ISSUE",
        "ratio": "1:1"
    }])
    factors = compute_adjustment_factors(ca, ["INFY"])
    adj_df = apply_adjustments(df, factors)
    
    # Guard #3 should return True
    assert unit_test_adjustments(adj_df) is True
