-- q08_factor_correlation.sql
-- Daily correlation of strategy returns with Nifty and IIMA factors
SELECT
    r.strategy,
    ROUND(CORR(r.net_return, f.mkt), 3)  AS corr_with_mkt,
    ROUND(CORR(r.net_return, f.smb), 3)  AS corr_with_smb,
    ROUND(CORR(r.net_return, f.hml), 3)  AS corr_with_hml,
    ROUND(CORR(r.net_return, f.wml), 3)  AS corr_with_wml,
    ROUND(CORR(r.net_return, n.daily_return), 3) AS corr_with_nifty50,
    COUNT(*)                              AS n_observations
FROM strategy_returns r
JOIN factors f ON r.return_date = f.factor_date
JOIN nifty50 n ON r.return_date = n.trade_date
WHERE r.cost_multiplier = 1.0 AND r.trial_id ILIKE '%main%'
GROUP BY r.strategy
ORDER BY r.strategy;
