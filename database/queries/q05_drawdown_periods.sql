-- q05_drawdown_periods.sql
-- Identify drawdown periods: start, end, depth, recovery date
WITH cum_returns AS (
    SELECT
        return_date, strategy, trial_id,
        EXP(SUM(LN(1 + net_return)) OVER (
            PARTITION BY strategy, trial_id ORDER BY return_date
        )) - 1                                    AS cum_return
    FROM strategy_returns
    WHERE cost_multiplier = 1.0 AND trial_id LIKE '%_main'
),
running_max AS (
    SELECT *,
        MAX(cum_return) OVER (
            PARTITION BY strategy, trial_id ORDER BY return_date
        )                                         AS peak
    FROM cum_returns
),
dd AS (
    SELECT *,
        (cum_return - peak) / (1 + peak)          AS drawdown
    FROM running_max
)
SELECT
    strategy,
    MIN(return_date) FILTER (WHERE drawdown = MIN(drawdown) OVER
        (PARTITION BY strategy))                  AS trough_date,
    ROUND(MIN(drawdown), 4)                       AS max_drawdown,
    ROUND(MIN(drawdown) * 100, 2)                 AS max_drawdown_pct
FROM dd
GROUP BY strategy
ORDER BY strategy;
