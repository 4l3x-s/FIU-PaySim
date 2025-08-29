SELECT
    step,
    (step - 1) / 24 AS day_num,
    (step - 1) % 24 AS hour_of_day,
  type,
  amount,
  nameOrig,
  nameDest,
  isFraud,
  isFlaggedFraud
FROM transactions;