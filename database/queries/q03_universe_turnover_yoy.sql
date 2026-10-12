-- q03_universe_turnover_yoy.sql
-- F&O universe: stocks entering and exiting each year
WITH prev_year AS (
    SELECT symbol,
           CAST(LEFT(trading_month, 4) AS INTEGER) AS year
    FROM universe
    GROUP BY symbol, year
),
current_year AS (
    SELECT symbol, year FROM prev_year
)
SELECT
    c.year,
    COUNT(DISTINCT c.symbol)                      AS total_stocks,
    COUNT(DISTINCT CASE WHEN p.symbol IS NULL THEN c.symbol END) AS new_entries,
    COUNT(DISTINCT CASE WHEN n.symbol IS NULL THEN c.symbol END) AS exits
FROM current_year c
LEFT JOIN prev_year p ON c.symbol = p.symbol AND c.year = p.year + 1
LEFT JOIN current_year n ON c.symbol = n.symbol AND n.year = c.year + 1
GROUP BY c.year
ORDER BY c.year;
