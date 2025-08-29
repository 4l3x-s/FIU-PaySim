-- Near-threshold band (structuring window) 9,000–9,999.99
-- Limit to retail-relevant types (same as your Python)
WITH base AS (
    SELECT
        (step - 1) / 24 AS day_num,
        (step - 1) % 24 AS hour_of_day
FROM transactions
WHERE type IN ('CASH_IN','PAYMENT','TRANSFER')
  AND amount >= 9000 AND amount < 10000
    )
SELECT
    day_num,
    hour_of_day,
    COUNT(*) AS n
FROM base
GROUP BY day_num, hour_of_day
ORDER BY day_num, hour_of_day;