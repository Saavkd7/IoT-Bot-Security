#!/bin/sh
set -e
ip link set eth0 up
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
CREATE TABLE IF NOT EXISTS sensor_events (
    id SERIAL PRIMARY KEY,
    sensor_id TEXT,
    topic TEXT,
    payload JSONB,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS actuator_confirmations (
    id SERIAL PRIMARY KEY,
    actuator_id TEXT,
    action TEXT,
    payload JSONB,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS iotbot_anomalies (
    id SERIAL PRIMARY KEY,
    type TEXT,
    target TEXT,
    description TEXT,
    payload JSONB,
    severity TEXT,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
EOF


