-- q04_cost_breakdown_by_year.sql
-- Average round-trip cost breakdown by year and cost component
SELECT
    YEAR(close_date)                              AS year,
    strategy,
    ROUND(AVG(cost_bps), 2)                       AS avg_total_cost_bps,
    COUNT(*)                                      AS n_trades,
    ROUND(AVG(gross_return - net_return) * 10000, 2) AS implied_cost_bps,
    ROUND(AVG(holding_days), 1)                   AS avg_hold_days
FROM trades
WHERE cost_multiplier = 1.0
GROUP BY year, strategy
ORDER BY year, strategy;
