-- q09_holding_period_distribution.sql
-- Distribution of trade holding periods: quartiles and outliers
SELECT
    strategy,
    trial_id,
    ROUND(MIN(holding_days), 0)          AS min_hold,
    ROUND(QUANTILE_CONT(holding_days, 0.25), 1) AS p25_hold,
    ROUND(QUANTILE_CONT(holding_days, 0.50), 1) AS median_hold,
    ROUND(QUANTILE_CONT(holding_days, 0.75), 1) AS p75_hold,
    ROUND(MAX(holding_days), 0)          AS max_hold,
    ROUND(AVG(holding_days), 1)          AS mean_hold,
    COUNT(*) FILTER (WHERE holding_days > 126) AS long_trades,
    COUNT(*)                              AS total_trades
FROM trades
WHERE cost_multiplier = 1.0
GROUP BY strategy, trial_id
ORDER BY strategy, trial_id;
