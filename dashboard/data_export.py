"""
Power BI Data Export Pipeline.
Exports modeled Star-Schema relational datasets from DuckDB to CSV for Power BI ingestion.
"""

import os
import duckdb
import pandas as pd
import numpy as np

def export_power_bi_star_schema(db_path="database/stat_arb.duckdb", output_dir="dashboard/data"):
    os.makedirs(output_dir, exist_ok=True)
    conn = duckdb.connect(db_path, read_only=True)
    
    print("Exporting Power BI Star Schema tables...")
    
    # 1. Dim_Date
    dates_df = conn.execute("""
        SELECT DISTINCT return_date AS date
        FROM strategy_returns
        ORDER BY date
    """).df()
    dates_df["date"] = pd.to_datetime(dates_df["date"])
    dates_df["year"] = dates_df["date"].dt.year
    dates_df["quarter"] = "Q" + dates_df["date"].dt.quarter.astype(str)
    dates_df["month"] = dates_df["date"].dt.month
    dates_df["month_name"] = dates_df["date"].dt.strftime("%b")
    dates_df["year_month"] = dates_df["date"].dt.strftime("%Y-%m")
    
    def assign_period(d):
        if d < pd.Timestamp("2015-01-01"):
            return "SP1: 2010-2014"
        elif d < pd.Timestamp("2020-01-01"):
            return "SP2: 2015-2019"
        else:
            return "SP3: 2020-2025"
    dates_df["sub_period"] = dates_df["date"].apply(assign_period)
    
    def assign_regime(d):
        if pd.Timestamp("2020-02-19") <= d <= pd.Timestamp("2020-03-31"):
            return "COVID-19 Crash"
        elif pd.Timestamp("2016-11-08") <= d <= pd.Timestamp("2016-12-31"):
            return "Demonetisation"
        elif pd.Timestamp("2022-01-01") <= d <= pd.Timestamp("2022-06-30"):
            return "2022 Global Selloff"
        elif d >= pd.Timestamp("2024-10-01"):
            return "Post-SEBI STT Hike (2024+)"
        else:
            return "Standard Market Regime"
    dates_df["market_regime"] = dates_df["date"].apply(assign_regime)
    dates_df.to_csv(os.path.join(output_dir, "dim_date.csv"), index=False)
    print(f" - dim_date.csv: {len(dates_df)} rows")

    # 2. Dim_Strategy
    dim_strat = pd.DataFrame([
        {
            "strategy_key": "Strategy_A_Main",
            "strategy_name": "Distance Pairs (Gatev et al. 2006)",
            "strategy_family": "Distance Metric Pairs",
            "methodology": "Top 20 Normalized SSD Pairs, 252d Formation, 2.0 Sigma Entry",
            "paper_citation": "Gatev, Goetzmann, Rouwenhorst (2006, RFS)",
            "target_holding_days": 126,
            "lookback_days": 252
        },
        {
            "strategy_key": "Strategy_B_Main",
            "strategy_name": "PCA-Residual Mean Reversion (Avellaneda-Lee 2010)",
            "strategy_family": "Statistical Factor Residuals",
            "methodology": "Rolling 252d PCA (k=5), OU Process AR(1), Rolling 60d s-score",
            "paper_citation": "Avellaneda & Lee (2010, Quantitative Finance)",
            "target_holding_days": 30,
            "lookback_days": 252
        },
        {
            "strategy_key": "Strategy_C_Ridge_Main",
            "strategy_name": "ML-Enhanced Residual Reversion (Guijarro-Ordonez echo)",
            "strategy_family": "Machine Learning Residuals",
            "methodology": "Expanding-Window Walk-Forward Ridge (10d Embargo), Quintile L/S",
            "paper_citation": "Guijarro-Ordonez, Pelger, Zanotti (2021, arXiv:2106.04028 echo)",
            "target_holding_days": 21,
            "lookback_days": 252
        }
    ])
    dim_strat.to_csv(os.path.join(output_dir, "dim_strategy.csv"), index=False)
    print(f" - dim_strategy.csv: {len(dim_strat)} rows")

    # 3. Dim_Cost_Scenario
    dim_cost = pd.DataFrame([
        {"cost_multiplier": 0.0, "scenario_name": "Gross Return (Zero Friction)", "description": "Theoretical frictionless benchmark"},
        {"cost_multiplier": 0.5, "scenario_name": "Low Friction (0.5x Baseline)", "description": "Proprietary desk / ultra-low execution cost"},
        {"cost_multiplier": 1.0, "scenario_name": "Institutional Baseline (1.0x)", "description": "Full statutory STT, stamp duty, NSE fees, GST, 5bps slippage"},
        {"cost_multiplier": 1.5, "scenario_name": "High Friction Stress (1.5x)", "description": "Adverse execution, retail brokerage, widened bid-ask"}
    ])
    dim_cost.to_csv(os.path.join(output_dir, "dim_cost_scenario.csv"), index=False)
    print(f" - dim_cost_scenario.csv: {len(dim_cost)} rows")

    # 4. Fact_Daily_Returns
    fact_returns = conn.execute("""
        SELECT
            r.return_date AS date,
            r.strategy AS strategy_key,
            r.cost_multiplier,
            r.gross_return,
            r.net_return,
            (r.gross_return - r.net_return) AS cost_drag,
            r.n_open_pairs,
            COALESCE(n.daily_return, 0.0) AS nifty50_return,
            COALESCE(f.rf, 0.00025) AS risk_free_rate
        FROM strategy_returns r
        LEFT JOIN nifty50 n ON r.return_date = n.trade_date
        LEFT JOIN factors f ON r.return_date = f.factor_date
        WHERE r.strategy IN ('Strategy_A_Main', 'Strategy_B_Main', 'Strategy_C_Ridge_Main')
        ORDER BY r.strategy, r.cost_multiplier, r.return_date
    """).df()
    fact_returns.to_csv(os.path.join(output_dir, "fact_daily_returns.csv"), index=False)
    print(f" - fact_daily_returns.csv: {len(fact_returns)} rows")

    # 5. Fact_Monthly_Summary
    fact_monthly = conn.execute("""
        WITH monthly AS (
            SELECT
                STRFTIME(return_date, '%Y-%m') AS year_month,
                strategy AS strategy_key,
                cost_multiplier,
                SUM(gross_return) AS monthly_gross_return,
                SUM(net_return) AS monthly_net_return,
                SUM(gross_return - net_return) AS monthly_cost_drag,
                AVG(n_open_pairs) AS avg_open_positions,
                COUNT(*) AS trading_days
            FROM strategy_returns
            WHERE strategy IN ('Strategy_A_Main', 'Strategy_B_Main', 'Strategy_C_Ridge_Main')
            GROUP BY year_month, strategy, cost_multiplier
        )
        SELECT * FROM monthly
        ORDER BY strategy_key, cost_multiplier, year_month
    """).df()
    fact_monthly.to_csv(os.path.join(output_dir, "fact_monthly_summary.csv"), index=False)
    print(f" - fact_monthly_summary.csv: {len(fact_monthly)} rows")

    # 6. Fact_Trades
    trades_df = conn.execute("""
        SELECT
            trade_id,
            strategy AS strategy_key,
            cost_multiplier,
            open_date,
            close_date,
            symbol,
            partner_symbol,
            holding_days,
            gross_return,
            net_return,
            cost_bps,
            close_signal,
            notional_inr,
            adtv_cr
        FROM trades
        ORDER BY open_date
    """).df()
    trades_df.to_csv(os.path.join(output_dir, "fact_trades.csv"), index=False)
    print(f" - fact_trades.csv: {len(trades_df)} rows")

    conn.close()
    print("All 6 Power BI relational datasets successfully exported to dashboard/data/!")

if __name__ == "__main__":
    export_power_bi_star_schema()
