"""
src/strategies/gatev.py
Phase 3 — Strategy A: Gatev et al. (2006) Distance Pairs Trading.
Methodological replication and out-of-sample extension for Indian F&O stocks.

Features:
- Formation period: 252 days (12 months) normalized cumulative total-return index
- Pair selection: Top N pairs by minimum Sum of Squared Deviations (SSD)
- Trading period: 126 days (6 months)
- Entry rule: Spread diverges by >= 2.0 * historical standard deviation
- Exit rule: Spread crosses 0.0 or reaches end of trading period
- Staggered cohorts: 6 overlapping monthly cohorts
- Capital methods: "committed" (1/N per pair) and "fully_invested"
- One-day-wait flag: Signal on day t executes at t+1 close (avoids execution look-ahead)
"""

import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from pathlib import Path
import yaml

LOG = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

CONF_A = CFG.get("strategy_a", {})


def normalize_price_series(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes each stock's price series to 1.0 on day 0 of formation window.
    prices: DataFrame indexed by trade_date, columns = symbols.
    """
    return prices / prices.iloc[0]


def compute_pair_ssd(norm_prices: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Sum of Squared Deviations (SSD) for all unique pairs in formation window.
    SSD(i, j) = sum_{t} (P_{i, t} - P_{j, t})^2
    Returns DataFrame with columns: ['stock_a', 'stock_b', 'ssd', 'spread_std']
    """
    symbols = list(norm_prices.columns)
    n = len(symbols)
    records = []

    for i in range(n):
        s_a = symbols[i]
        p_a = norm_prices[s_a].values
        for j in range(i + 1, n):
            s_b = symbols[j]
            p_b = norm_prices[s_b].values
            diff = p_a - p_b
            ssd = np.sum(diff ** 2)
            std_spread = np.std(diff, ddof=1)
            records.append({
                "stock_a": s_a,
                "stock_b": s_b,
                "ssd": float(ssd),
                "spread_std": float(std_spread) if std_spread > 1e-8 else 1e-8
            })

    df = pd.DataFrame(records)
    return df.sort_values("ssd").reset_index(drop=True)


def select_pairs(ssd_df: pd.DataFrame, top_n: int = 20,
                 sector_map: Optional[Dict[str, str]] = None,
                 sector_restrict: bool = False) -> pd.DataFrame:
    """
    Selects top N pairs by lowest SSD.
    If sector_restrict is True, both stocks must belong to the same sector.
    """
    if sector_restrict and sector_map:
        filtered = []
        for _, row in ssd_df.iterrows():
            sec_a = sector_map.get(row["stock_a"])
            sec_b = sector_map.get(row["stock_b"])
            if sec_a and sec_b and sec_a == sec_b:
                filtered.append(row)
        df_use = pd.DataFrame(filtered)
    else:
        df_use = ssd_df

    return df_use.head(top_n).reset_index(drop=True)


def simulate_pair_trading(
    p_a_series: pd.Series,
    p_b_series: pd.Series,
    spread_std: float,
    entry_sigma: float = 2.0,
    exit_threshold: float = 0.0,
    one_day_wait: bool = False,
    allow_reopen: bool = True
) -> Tuple[pd.Series, List[dict]]:
    """
    Simulates trading for a single pair over the trading window.
    Normalized prices start at 1.0 on day 0 of the trading period.
    Spread S_t = p_a(t) - p_b(t).
    
    Returns:
      daily_returns: pd.Series of daily P&L return for the pair
      trades: list of trade dictionaries
    """
    dates = p_a_series.index
    n_days = len(dates)
    if n_days < 2:
        return pd.Series(0.0, index=dates), []

    # Normalize within trading window
    p_a = (p_a_series / p_a_series.iloc[0]).values
    p_b = (p_b_series / p_b_series.iloc[0]).values
    spread = p_a - p_b

    # Return series for stock A and B
    r_a = p_a_series.pct_change().fillna(0.0).values
    r_b = p_b_series.pct_change().fillna(0.0).values

    # Position state: 0 = Flat, +1 = Long A / Short B, -1 = Short A / Long B
    position = 0
    pending_position = 0
    pair_returns = np.zeros(n_days)
    trades = []
    open_idx = None

    threshold_up = entry_sigma * spread_std
    threshold_down = -entry_sigma * spread_std

    for t in range(n_days):
        # 1. Apply any pending trade execution from previous day's signal (one-day-wait)
        if one_day_wait:
            if pending_position != position:
                if position != 0 and pending_position == 0 and open_idx is not None:
                    # Close trade
                    trades.append({
                        "open_date": dates[open_idx],
                        "close_date": dates[t],
                        "holding_days": t - open_idx,
                        "position": position,
                        "exit_spread": spread[t]
                    })
                    open_idx = None
                elif position == 0 and pending_position != 0:
                    open_idx = t
                position = pending_position

        # 2. Compute P&L for day t if holding a position
        if position == 1:
            # Long A, Short B
            pair_returns[t] = 0.5 * r_a[t] - 0.5 * r_b[t]
        elif position == -1:
            # Short A, Long B
            pair_returns[t] = -0.5 * r_a[t] + 0.5 * r_b[t]

        # 3. Check signal logic at day t close
        s_t = spread[t]
        target_pos = position if not one_day_wait else pending_position

        if target_pos == 0:
            if allow_reopen or len(trades) == 0:
                if s_t >= threshold_up:
                    # Spread too high: Short A, Long B
                    if one_day_wait:
                        pending_position = -1
                    else:
                        position = -1
                        open_idx = t
                elif s_t <= threshold_down:
                    # Spread too low: Long A, Short B
                    if one_day_wait:
                        pending_position = 1
                    else:
                        position = 1
                        open_idx = t
        elif target_pos == 1:
            # Long A, Short B: close when spread crosses exit_threshold (0.0) from below
            if s_t >= exit_threshold:
                if one_day_wait:
                    pending_position = 0
                else:
                    trades.append({
                        "open_date": dates[open_idx],
                        "close_date": dates[t],
                        "holding_days": t - open_idx,
                        "position": position,
                        "exit_spread": s_t
                    })
                    position = 0
                    open_idx = None
        elif target_pos == -1:
            # Short A, Long B: close when spread crosses exit_threshold (0.0) from above
            if s_t <= exit_threshold:
                if one_day_wait:
                    pending_position = 0
                else:
                    trades.append({
                        "open_date": dates[open_idx],
                        "close_date": dates[t],
                        "holding_days": t - open_idx,
                        "position": position,
                        "exit_spread": s_t
                    })
                    position = 0
                    open_idx = None

    # Close any open trade at end of trading period
    if position != 0 and open_idx is not None:
        trades.append({
            "open_date": dates[open_idx],
            "close_date": dates[-1],
            "holding_days": n_days - 1 - open_idx,
            "position": position,
            "exit_spread": spread[-1]
        })

    return pd.Series(pair_returns, index=dates), trades


def run_gatev_cohort(
    prices_formation: pd.DataFrame,
    prices_trading: pd.DataFrame,
    top_n: int = 20,
    entry_sigma: float = 2.0,
    exit_threshold: float = 0.0,
    one_day_wait: bool = False,
    capital_method: str = "committed",
    sector_map: Optional[Dict[str, str]] = None,
    sector_restrict: bool = False
) -> Tuple[pd.Series, pd.DataFrame, List[dict]]:
    """
    Runs Gatev pairs trading for a single cohort.
    Returns:
      cohort_returns: daily returns series
      selected_pairs: DataFrame of top pairs
      all_trades: list of trade execution records
    """
    # 1. Normalize formation prices & compute SSD
    norm_form = normalize_price_series(prices_formation)
    ssd_df = compute_pair_ssd(norm_form)
    pairs = select_pairs(ssd_df, top_n=top_n, sector_map=sector_map, sector_restrict=sector_restrict)

    # 2. Simulate trading for each pair
    pair_returns_dict = {}
    all_trades = []

    for _, row in pairs.iterrows():
        s_a, s_b = row["stock_a"], row["stock_b"]
        std_sp = row["spread_std"]
        if s_a not in prices_trading.columns or s_b not in prices_trading.columns:
            continue
        p_a = prices_trading[s_a]
        p_b = prices_trading[s_b]

        ret_series, trades = simulate_pair_trading(
            p_a, p_b, std_sp,
            entry_sigma=entry_sigma,
            exit_threshold=exit_threshold,
            one_day_wait=one_day_wait
        )
        pair_returns_dict[f"{s_a}_{s_b}"] = ret_series
        for tr in trades:
            tr["pair"] = f"{s_a}_{s_b}"
            tr["stock_a"] = s_a
            tr["stock_b"] = s_b
            all_trades.append(tr)

    pair_matrix = pd.DataFrame(pair_returns_dict)

    # 3. Capital allocation
    if capital_method == "committed":
        # Divide by top_n pairs regardless of whether they are active
        cohort_returns = pair_matrix.sum(axis=1) / top_n
    else:  # fully_invested
        # Weight only active pairs
        active_counts = (pair_matrix != 0).sum(axis=1)
        cohort_returns = pair_matrix.sum(axis=1) / np.maximum(active_counts, 1)

    return cohort_returns, pairs, all_trades
