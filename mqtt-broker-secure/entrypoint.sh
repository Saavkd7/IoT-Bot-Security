#!/bin/sh
echo "[Entrypoint]  Starting dynamic Mosquitto configuration..."

if [ "$ENABLE_TLS" = "true" ] && [ "$ENABLE_AUTH" = "true" ]; then
    echo "[Entrypoint]  TLS + Auth"
    cp /mosquitto/config/mosquitto_tls_auth.conf /mosquitto/config/mosquitto.conf
elif [ "$ENABLE_TLS" = "true" ]; then
    echo "[Entrypoint]  TLS only"
    cp /mosquitto/config/mosquitto_tls_only.conf /mosquitto/config/mosquitto.conf
elif [ "$ENABLE_AUTH" = "true" ]; then
    echo "[Entrypoint]  Auth only (no TLS)"
    cp /mosquitto/config/mosquitto_auth_only.conf /mosquitto/config/mosquitto.conf
else
    echo "[Entrypoint]  Open mode (no TLS, no Auth)"
    cp /mosquitto/config/mosquitto_open.conf /mosquitto/config/mosquitto.conf
fi

echo "[Entrypoint]  Launching Mosquitto with:"
cat /mosquitto/config/mosquitto.conf

exec mosquitto -c /mosquitto/config/mosquitto.conf

