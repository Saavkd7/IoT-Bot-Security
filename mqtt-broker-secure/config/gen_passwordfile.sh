#!/bin/sh
echo "[Docker Build] Generating Mosquitto passwordfile..."

mosquitto_passwd -b -c /mosquitto/config/passwordfile actuator_user actuatorpass
mosquitto_passwd -b /mosquitto/config/passwordfile sensor_user sensorpass
mosquitto_passwd -b /mosquitto/config/passwordfile hub_user hubpass
mosquitto_passwd -b /mosquitto/config/passwordfile iotbot_user iotbotpass

chmod 0600 /mosquitto/config/passwordfile
echo "[Docker Build] Passwordfile ready"

