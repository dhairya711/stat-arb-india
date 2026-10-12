-- q02_monthly_pnl_rolling.sql
-- Monthly PnL, 12-month rolling return, and cumulative return for Main specifications
WITH monthly AS (
    SELECT
        STRFTIME(return_date, '%Y-%m') AS month,
        strategy,
        cost_multiplier,
        SUM(net_return) AS monthly_net_return
    FROM strategy_returns
    WHERE trial_id ILIKE '%main%'
    GROUP BY month, strategy, cost_multiplier
)
SELECT
    month,
    strategy,
    cost_multiplier,
    ROUND(monthly_net_return, 4) AS monthly_net_return,
    ROUND(AVG(monthly_net_return) OVER (
        PARTITION BY strategy, cost_multiplier
        ORDER BY month
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    ), 6) AS rolling_12m_avg,
    ROUND(SUM(monthly_net_return) OVER (
        PARTITION BY strategy, cost_multiplier
        ORDER BY month
    ), 6) AS cumulative_net_return
FROM monthly
ORDER BY strategy, cost_multiplier, month;
