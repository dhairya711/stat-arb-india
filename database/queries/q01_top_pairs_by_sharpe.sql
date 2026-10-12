-- q01_top_pairs_by_sharpe.sql
-- Top 10 Strategy A pairs by annualised net Sharpe per calendar year
SELECT
    YEAR(close_date)                              AS year,
    symbol || '-' || partner_symbol               AS pair,
    COUNT(*)                                      AS n_trades,
    ROUND(AVG(gross_return) * 252, 4)             AS gross_return_pa,
    ROUND(AVG(net_return) * 252, 4)               AS net_return_pa,
    ROUND(AVG(net_return) / NULLIF(STDDEV(net_return), 0) * SQRT(252), 3) AS net_sharpe_annualised,
    ROUND(AVG(holding_days), 1)                   AS avg_hold_days
FROM trades
WHERE (strategy ILIKE '%gatev%' OR strategy ILIKE 'A%')
  AND cost_multiplier = 1.0
GROUP BY year, pair
HAVING n_trades >= 1
QUALIFY ROW_NUMBER() OVER (PARTITION BY year ORDER BY net_sharpe_annualised DESC) <= 10
ORDER BY year, net_sharpe_annualised DESC;
