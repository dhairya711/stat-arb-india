-- q02_monthly_pnl_rolling.sql
-- Monthly P&L with 3-month and 12-month rolling average net return
SELECT
    return_date,
    strategy,
    cost_multiplier,
    ROUND(net_return, 6)                          AS net_return,
    ROUND(AVG(net_return) OVER (
        PARTITION BY strategy, cost_multiplier
        ORDER BY return_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 6)                                         AS rolling_3m_avg,
    ROUND(AVG(net_return) OVER (
        PARTITION BY strategy, cost_multiplier
        ORDER BY return_date
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    ), 6)                                         AS rolling_12m_avg,
    ROUND(SUM(net_return) OVER (
        PARTITION BY strategy, cost_multiplier
        ORDER BY return_date
    ), 6)                                         AS cumulative_net_return
FROM strategy_returns
WHERE trial_id LIKE '%_main'
ORDER BY strategy, return_date;
