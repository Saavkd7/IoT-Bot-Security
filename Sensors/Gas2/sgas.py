#!/usr/bin/env python3
# Minimal gas sensor simulator

import os, json, time, random
import paho.mqtt.client as mqtt
from datetime import datetime

BROKER      = os.getenv("BROKER_ADDRESS", "mqtt-broker")
PORT        = 8883 if os.getenv("ENABLE_TLS", "false").lower() == "true" else 1883
USERNAME    = os.getenv("MQTT_USERNAME", "")
PASSWORD    = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS  = os.getenv("ENABLE_TLS", "false").lower() == "true"
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"

DEVICE_ID   = "sensor_gas_01"
TOPIC       = "building/zone3/gas/detection"
HEARTBEAT   = "hub/heartbeat"
last_hb     = time.time()

def now():
    return datetime.now().strftime("%d/%m/%y %H:%M:%S")

def on_connect(client, userdata, flags, rc):
    print("[Gas Sensor] Connected.")
    client.subscribe(HEARTBEAT)

def on_message(client, userdata, msg):
    global last_hb
    if msg.topic == HEARTBEAT:
        last_hb = time.time()

client = mqtt.Client()
if ENABLE_AUTH:
    client.username_pw_set(USERNAME, PASSWORD)
if ENABLE_TLS:
    client.tls_set(ca_certs="/mosquitto/certs/ca.crt")

client.on_connect = on_connect
client.on_message = on_message

while True:
    try:
        client.connect(BROKER, port=PORT)
        break
    except Exception as e:
        print(f"[Gas Sensor] Retry: {e}")
        time.sleep(3)

client.loop_start()
print("[Gas Sensor] Sending gas data...")

while True:
    if time.time() - last_hb <= 10:
        value = round(random.uniform(300, 1200), 2)
        msg = {
            "device_id": DEVICE_ID,
            "sensor": "gas",
            "value": value,
            "timestamp": now()
        }
        client.publish(TOPIC, json.dumps(msg))
        print(f"[Gas Sensor] {value} ppm")
    else:
        print("[Gas Sensor] Paused (no heartbeat)")
    time.sleep(6)

