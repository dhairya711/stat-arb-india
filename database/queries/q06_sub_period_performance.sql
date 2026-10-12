-- q06_sub_period_performance.sql
-- Strategy performance across pre-registered sub-periods (SP1, SP2, SP3)
SELECT
    strategy,
    cost_multiplier,
    CASE
        WHEN return_date BETWEEN '2010-01-01' AND '2014-12-31' THEN 'SP1: 2010-2014'
        WHEN return_date BETWEEN '2015-01-01' AND '2019-12-31' THEN 'SP2: 2015-2019'
        WHEN return_date BETWEEN '2020-01-01' AND '2025-12-31' THEN 'SP3: 2020-2025'
    END                                           AS sub_period,
    COUNT(*)                                      AS n_months,
    ROUND(AVG(gross_return) * 12, 4)             AS gross_return_pa,
    ROUND(AVG(net_return) * 12, 4)               AS net_return_pa,
    ROUND(STDDEV(net_return) * SQRT(12), 4)      AS net_vol_pa,
    ROUND(AVG(net_return) / NULLIF(STDDEV(net_return), 0) * SQRT(12), 3) AS net_sharpe_pa,
    ROUND(AVG(n_open_pairs), 1)                  AS avg_open_pairs
FROM strategy_returns
WHERE trial_id LIKE '%_main'
  AND sub_period IS NOT NULL
GROUP BY strategy, cost_multiplier, sub_period
ORDER BY strategy, cost_multiplier, sub_period;
