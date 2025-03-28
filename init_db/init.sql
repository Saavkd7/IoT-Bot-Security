CREATE TABLE IF NOT EXISTS network_logs (
    id SERIAL PRIMARY KEY,
    device_id TEXT,
    event TEXT,
    payload JSONB,
    timestamp DOUBLE PRECISION
);

