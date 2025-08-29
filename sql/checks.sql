SELECT 'rows_total'      AS metric, COUNT(*)                     AS val FROM transactions
UNION ALL
SELECT 'near_9k_10k',           COUNT(*)                         FROM transactions WHERE amount >= 9000 AND amount < 10000
UNION ALL
SELECT 'customer_accounts',     COUNT(DISTINCT nameOrig)         FROM transactions WHERE nameOrig LIKE 'C%'
UNION ALL
SELECT 'counterparties_total',  COUNT(DISTINCT nameDest)         FROM transactions;