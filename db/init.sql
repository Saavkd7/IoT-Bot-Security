CREATE TABLE IF NOT EXISTS sensor_data (
    id SERIAL PRIMARY KEY,
    device_id TEXT,
    payload JSONB,
    timestamp TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS actuator_actions (
    id SERIAL PRIMARY KEY,
    device_id TEXT,
    payload JSONB,
    timestamp TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS anomaly_logs (
    id SERIAL PRIMARY KEY,
    device_id TEXT,
    payload JSONB,
    timestamp TIMESTAMPTZ
);


CREATE TABLE IF NOT EXISTS registered_devices (
    device_id TEXT PRIMARY KEY,
    registered_at TIMESTAMPTZ DEFAULT now()
);

