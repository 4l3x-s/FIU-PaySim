-- All transactions by day_num × hour_of_day
WITH base AS (
    SELECT
        (step - 1) / 24 AS day_num,
        (step - 1) % 24 AS hour_of_day
FROM transactions
    )
SELECT
    day_num,
    hour_of_day,
    COUNT(*) AS n
FROM base
GROUP BY day_num, hour_of_day
ORDER BY day_num, hour_of_day;