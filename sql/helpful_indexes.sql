-- Speed up common filters/joins
CREATE INDEX IF NOT EXISTS idx_tx_type         ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_tx_amount       ON transactions(amount);
CREATE INDEX IF NOT EXISTS idx_tx_step         ON transactions(step);
CREATE INDEX IF NOT EXISTS idx_tx_nameorig     ON transactions(nameOrig);
CREATE INDEX IF NOT EXISTS idx_tx_namedest     ON transactions(nameDest);