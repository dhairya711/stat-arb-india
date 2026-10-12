-- q10_cost_sensitivity.sql
-- Net Sharpe at 0%, 50%, 100%, 150% of baseline costs — the key sensitivity table
SELECT
    strategy,
    cost_multiplier,
    COUNT(DISTINCT return_date)            AS n_months,
    ROUND(AVG(gross_return) * 12, 4)      AS gross_return_pa,
    ROUND(AVG(net_return) * 12, 4)        AS net_return_pa,
    ROUND(AVG(net_return) / NULLIF(STDDEV(net_return), 0) * SQRT(12), 3) AS net_sharpe,
    ROUND((AVG(gross_return) - AVG(net_return)) * 12, 4) AS total_cost_pa
FROM strategy_returns
WHERE trial_id LIKE '%_main'
  AND cost_multiplier IN (0.0, 0.5, 1.0, 1.5)
GROUP BY strategy, cost_multiplier
ORDER BY strategy, cost_multiplier;
