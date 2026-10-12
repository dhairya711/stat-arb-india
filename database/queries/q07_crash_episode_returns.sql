-- q07_crash_episode_returns.sql
-- Returns during pre-registered crash/regime episodes
WITH episodes AS (
    SELECT 'COVID_crash' AS episode, DATE '2020-02-19' AS start_date, DATE '2020-03-31' AS end_date
    UNION ALL
    SELECT 'Demonetisation', DATE '2016-11-08', DATE '2016-12-31'
    UNION ALL
    SELECT '2022_selloff', DATE '2022-01-01', DATE '2022-06-30'
    UNION ALL
    SELECT 'Post_SEBI_2024', DATE '2024-10-01', DATE '2025-12-31'
)
SELECT
    e.episode,
    r.strategy,
    COUNT(*) AS n_days,
    ROUND(SUM(r.net_return) * 100, 2)   AS total_net_return_pct,
    ROUND(AVG(r.net_return) * 252 * 100, 2) AS annualised_net_pct,
    ROUND(AVG(r.net_return) / NULLIF(STDDEV(r.net_return), 0) * SQRT(252), 3) AS sharpe
FROM episodes e
JOIN strategy_returns r
    ON r.return_date BETWEEN e.start_date AND e.end_date
WHERE r.cost_multiplier = 1.0 AND r.trial_id LIKE '%_main'
GROUP BY e.episode, r.strategy
ORDER BY e.episode, r.strategy;
