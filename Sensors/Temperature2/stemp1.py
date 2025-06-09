import os
import json
import time
import ssl
import math
import random
import hmac
import hashlib
import paho.mqtt.client as mqtt
from datetime import datetime

# === CONFIG ===
BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS = os.getenv("ENABLE_TLS", "false").lower() == "true"
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
ENABLE_HMAC = os.getenv("ENABLE_HMAC", "true").lower() == "true"
PORT = 8883 if ENABLE_TLS else 1883
HMAC_SECRET = os.getenv("HMAC_SECRET", "defaultsecret").encode()

SENSOR_TOPIC = "building/zone2/temperature/room1"
HEARTBEAT_TOPIC = "hub/heartbeat"
DEVICE_ID = "sensor_temp_01"
last_heartbeat = time.time()
current_temp = 22.0

# === UTILS ===
def get_season():
    month = datetime.now().month
    return ["winter", "spring", "summer", "autumn"][(month % 12) // 3]

def get_day_factor():
    return math.cos((datetime.now().hour - 14) / 6) * -2

def simulate_temperature(current, season):
    baseline = {
        "winter": 18.0, "spring": 21.0, "summer": 25.0, "autumn": 20.0
    }[season]
    variation = get_day_factor()
    noise = random.uniform(-0.2, 0.2)
    drift = (baseline + variation - current) * 0.05
    return round(current + drift + noise, 2)

def get_timestamp():
    return datetime.now().strftime("%d/%m/%y %H:%M")

def sign(payload):
    if not ENABLE_HMAC:
        return ""
    data = json.dumps({k: payload[k] for k in sorted(payload)}, separators=(',', ':'), sort_keys=True).encode()
    return hmac.new(HMAC_SECRET, data, hashlib.sha256).hexdigest()

# === MQTT CALLBACKS ===
def on_connect(client, userdata, flags, rc):
    print("[Temp Sensor] Connected.")
    client.subscribe(HEARTBEAT_TOPIC)

def on_message(client, userdata, msg):
    global last_heartbeat
    if msg.topic == HEARTBEAT_TOPIC:
        last_heartbeat = time.time()

# === CLIENT SETUP ===
client = mqtt.Client()
if ENABLE_AUTH:
    client.username_pw_set(USERNAME, PASSWORD)
if ENABLE_TLS:
    client.tls_set(ca_certs="/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)
client.on_connect = on_connect
client.on_message = on_message
client.reconnect_delay_set(1, 30)

# === CONNECT LOOP ===
while True:
    try:
        client.connect(BROKER, port=PORT)
        break
    except Exception as e:
        print(f"[Temp Sensor]  Retrying connection: {e}")
        time.sleep(3)

client.loop_start()
print("[Temp Sensor]  Waiting for hub heartbeat...")

# === MAIN LOOP ===
while True:
    if time.time() - last_heartbeat <= 10:
        season = get_season()
        current_temp = simulate_temperature(current_temp, season)
        payload = {
            "device_id": DEVICE_ID,
            "sensor": "temperature",
            "value": current_temp,
            "timestamp": get_timestamp()
        }
        if ENABLE_HMAC:
            payload["hmac"] = sign(payload)
        client.publish(SENSOR_TOPIC, json.dumps(payload))
        print(f"[Temp Sensor]  Temp: {current_temp} °C")
    else:
        print("[Temp Sensor] Paused (hub offline)")
    time.sleep(5)

