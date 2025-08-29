-- Core per-account features (SQL-computable subset)
WITH base AS (
    SELECT
        nameOrig,
        amount,
        nameDest,
        CASE WHEN amount >= 9000 AND amount < 10000 THEN 1 ELSE 0 END AS near_thresh,
        isFraud,
        isFlaggedFraud
    FROM transactions
    WHERE nameOrig LIKE 'C%'   -- keep customer-originated accounts
)
SELECT
    nameOrig                                   AS account,
    COUNT(*)                                   AS n_tx,
    SUM(amount)                                AS amt_sum,
    AVG(amount)                                AS amt_mean,
    MAX(amount)                                AS amt_max,
    SUM(near_thresh)                           AS near_n,
    1.0 * SUM(near_thresh) / NULLIF(COUNT(*),0) AS near_pct,
    SUM(isFraud)                               AS fraud_n,
    SUM(isFlaggedFraud)                        AS flagged_n,
    COUNT(DISTINCT nameDest)                   AS cp_diversity
FROM base
GROUP BY nameOrig
ORDER BY n_tx DESC;