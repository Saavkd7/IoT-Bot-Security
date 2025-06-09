#!/usr/bin/env python3
# SENSOR: sgas.py  (Gas sensor – realistic simulation + HMAC + heartbeat-aware)

import os
import json
import time
import ssl
import random
import hmac
import hashlib
import paho.mqtt.client as mqtt
from datetime import datetime

# CONFIGURATION 
BROKER        = os.getenv("BROKER_ADDRESS", "mqtt-broker")
PORT          = 8883 if os.getenv("ENABLE_TLS", "false").lower() == "true" else 1883
USERNAME      = os.getenv("MQTT_USERNAME", "")
PASSWORD      = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS    = os.getenv("ENABLE_TLS",  "false").lower() == "true"
ENABLE_AUTH   = os.getenv("ENABLE_AUTH", "false").lower() == "true"
ENABLE_HMAC   = os.getenv("ENABLE_HMAC", "true" ).lower() == "true"
HMAC_SECRET   = os.getenv("HMAC_SECRET", "123iot45").encode()

DEVICE_ID     = "sensor_gas_01"
TOPIC         = "building/zone3/gas/detection"
HEARTBEAT     = "hub/heartbeat"
last_hb       = time.time()

# TOOLS 
def now_str():
    return datetime.now().strftime("%d/%b/%y %H:%M:%S")

def sign(pkt: dict) -> str:
    if not ENABLE_HMAC:
        return ""
    raw = json.dumps({k: pkt[k] for k in sorted(pkt)}, separators=(',', ':'), sort_keys=True).encode()
    return hmac.new(HMAC_SECRET, raw, hashlib.sha256).hexdigest()

# GAS SIMULATION 

gas_level = 400.0  # Starting CO2 ppm

def simulate_gas(current_level):
    # Choose a realistic indoor range with some probability of spikes
    target = random.choices(
        [400, 600, 800, 1000, 1200],
        weights=[40, 30, 15, 10, 5],
        k=1
    )[0]
    drift = (target - current_level) * 0.05  # smooth change
    noise = random.uniform(-5, 5)  # small random fluctuation
    return round(current_level + drift + noise, 2)

# MQTT PREDEFINE CALLBACKS 

def on_connect(client, userdata, flags, rc):
    print("[Gas Sensor]  Connected.")
    client.subscribe(HEARTBEAT)

def on_message(client, userdata, msg):
    global last_hb
    if msg.topic == HEARTBEAT:
        last_hb = time.time()

# MQTT CLIENT SETUP 

client = mqtt.Client()
if ENABLE_AUTH:
    client.username_pw_set(USERNAME, PASSWORD)
if ENABLE_TLS:
    client.tls_set("/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)

client.on_connect  = on_connect
client.on_message  = on_message
client.reconnect_delay_set(1, 30)

while True:
    try:
        client.connect(BROKER, port=PORT)
        break
    except Exception as e:
        print(f"[Gas Sensor] 🔁 Retry: {e}")
        time.sleep(3)

client.loop_start()
print("[Gas Sensor] 💨 Sending gas readings...")

# LOOP 

while True:
    if time.time() - last_hb <= 10:  # hub is alive
        gas_level = simulate_gas(gas_level)
        pkt = {
            "device_id": DEVICE_ID,
            "sensor"   : "gas",
            "value"    : gas_level,
            "timestamp": now_str()
        }
        if ENABLE_HMAC:
            pkt["hmac"] = sign(pkt)
        client.publish(TOPIC, json.dumps(pkt))
        print(f"[Gas Sensor] 📤 {gas_level} ppm")
    else:
        print("[Gas Sensor] ⏸ Paused (hub offline)")
    time.sleep(6)

