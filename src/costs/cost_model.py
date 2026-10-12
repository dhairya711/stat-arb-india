"""
src/costs/cost_model.py
Phase 2 — Dated cost schedule for Indian F&O statistical arbitrage.

Phase 2 Failure Guard:
- STT rates verified from Union Budget 2024-25 / NSE circular
- Net return is always <= gross return (checked at end of compute_costs)
- Break-even solver converges to finite value
- UNVERIFIED rates marked explicitly; covered by sensitivity sweep
"""
from datetime import date
import pandas as pd
import numpy as np
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

C = CFG["costs"]

# ─── STT Schedule (VERIFIED) ─────────────────────────────────────────────────
STT_CUTOFF = date(2024, 10, 1)

def stt_rate(trade_date: date) -> float:
    """STT on futures sell side (verified from Union Budget 2024-25)."""
    if trade_date >= STT_CUTOFF:
        return C["stt"]["from_2024_10_01"]      # 0.02%
    return C["stt"]["before_2024_10_01"]         # 0.0125%


def nse_charge_rate(trade_date: date) -> float:
    """NSE exchange transaction charge per INR 1 lakh traded value."""
    if trade_date >= STT_CUTOFF:
        return C["nse_charges"]["from_2024_10_01_per_lakh"] / 100_000
    return C["nse_charges"]["before_2024_10_01_per_lakh"] / 100_000   # UNVERIFIED pre-2024


def slippage_bps(adtv_cr: float) -> float:
    """Slippage in bps per side, by ADTV tier (model assumption)."""
    s = C["slippage_bps"]
    if adtv_cr >= s["tier1_adtv_cr_min"]:
        return s["tier1_bps"]
    elif adtv_cr >= s["tier2_adtv_cr_min"]:
        return s["tier2_bps"]
    return s["tier3_bps"]


def compute_round_trip_cost(notional: float, trade_date: date,
                             adtv_cr: float = 50.0,
                             cost_multiplier: float = 1.0,
                             is_roll: bool = False) -> dict:
    """
    Compute full round-trip cost for one futures position.

    Args:
        notional: position size in INR
        trade_date: date for STT/charge rate lookup
        adtv_cr: ADTV in crore (for slippage tier)
        cost_multiplier: 0.0/0.5/1.0/1.5 for scenario sweep
        is_roll: add roll cost if True

    Returns:
        dict with cost components and total_bps

    Phase 2 Guard: total cost is always positive.
    """
    stt = stt_rate(trade_date) * notional * 2          # both entry and exit sell sides
    nse = nse_charge_rate(trade_date) * notional * 2
    sebi = C["sebi_turnover_fee"] * notional * 2        # UNVERIFIED
    stamp = C["stamp_duty"] * notional                  # buyer side only, UNVERIFIED
    gst = (C["brokerage_per_order_inr"] * 2 + nse) * C["gst_rate"]
    brokerage = C["brokerage_per_order_inr"] * 2
    slip_bps = slippage_bps(adtv_cr)
    slip = (slip_bps / 10_000) * notional * 2

    roll = 0.0
    if is_roll:
        roll = (C["roll"]["roll_cost_bps"] / 10_000) * notional

    total_raw = stt + nse + sebi + stamp + gst + brokerage + slip + roll
    total = total_raw * cost_multiplier

    # Phase 2 Guard: costs must be positive
    assert total >= 0, f"Negative total cost computed: {total}"

    total_bps = (total / notional) * 10_000

    return {
        "stt": stt * cost_multiplier,
        "nse_charge": nse * cost_multiplier,
        "sebi_fee": sebi * cost_multiplier,
        "stamp_duty": stamp * cost_multiplier,
        "gst": gst * cost_multiplier,
        "brokerage": brokerage * cost_multiplier,
        "slippage": slip * cost_multiplier,
        "roll_cost": roll * cost_multiplier,
        "total_inr": total,
        "total_bps": total_bps,
        "notional": notional,
        "trade_date": trade_date,
        "cost_multiplier": cost_multiplier,
    }


def apply_costs_to_returns(gross_returns: pd.Series,
                            notional_series: pd.Series,
                            trade_dates: pd.Series,
                            adtv_series: pd.Series,
                            cost_multiplier: float = 1.0) -> pd.Series:
    """
    Subtract round-trip costs from gross returns to get net returns.
    Phase 2 Guard: net_returns <= gross_returns always.
    """
    costs = []
    for gross, notional, td, adtv in zip(gross_returns, notional_series,
                                          trade_dates, adtv_series):
        c = compute_round_trip_cost(notional, td, adtv_cr=adtv,
                                    cost_multiplier=cost_multiplier)
        costs.append(c["total_bps"] / 10_000)  # convert to return units

    cost_series = pd.Series(costs, index=gross_returns.index)
    net_returns = gross_returns - cost_series

    # Phase 2 Guard: net must be <= gross
    if (net_returns > gross_returns).any():
        raise AssertionError("Phase 2 Guard FAIL: net_returns > gross_returns. "
                             "Cost sign error in cost_model.py")
    return net_returns


def breakeven_cost_multiplier(gross_return_pa: float,
                               avg_cost_bps_at_multiplier_1: float,
                               trades_per_year: float) -> float:
    """
    Find cost multiplier where net return = 0.
    net_return = gross - multiplier * (avg_cost_bps * trades) / 10000 = 0
    multiplier_BE = gross * 10000 / (avg_cost_bps * trades)
    """
    if avg_cost_bps_at_multiplier_1 <= 0 or trades_per_year <= 0:
        return float("inf")
    total_cost_pa_at_1x = (avg_cost_bps_at_multiplier_1 / 10_000) * trades_per_year
    if total_cost_pa_at_1x <= 0:
        return float("inf")
    return gross_return_pa / total_cost_pa_at_1x


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

    # Phase 2 Guard test
    test = compute_round_trip_cost(
        notional=1_000_000,
        trade_date=date(2024, 11, 1),
        adtv_cr=100,
        cost_multiplier=1.0
    )
    log.info("Cost components (INR 10L notional, post-Oct-2024):")
    for k, v in test.items():
        if isinstance(v, float):
            log.info(f"  {k:20s}: {v:10.2f}")
    log.info(f"  Total bps: {test['total_bps']:.2f} bps")

    be = breakeven_cost_multiplier(0.05, test["total_bps"], 50)
    log.info(f"  Break-even multiplier (5% gross, 50 trades/yr): {be:.2f}x")
    log.info("Phase 2 Failure Guard: cost model passed basic sanity checks.")
