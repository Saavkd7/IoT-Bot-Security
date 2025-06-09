# SENSOR: sgas.py (Gas sensor with HMAC and heartbeat handling)
import os
import json
import time
import ssl
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

DEVICE_ID = "sensor_gas_01"
TOPIC = "building/zone3/gas/detection"
HEARTBEAT_TOPIC = "hub/heartbeat"
last_heartbeat = time.time()

# === UTILS ===
def get_timestamp():
    return datetime.now().strftime("%d/%b/%y %H:%M:%S")

def sign(pkt):
    if not ENABLE_HMAC:
        return ""
    data = json.dumps({k: pkt[k] for k in sorted(pkt)}, separators=(',', ':'), sort_keys=True).encode()
    return hmac.new(HMAC_SECRET, data, hashlib.sha256).hexdigest()

# === MQTT CALLBACKS ===
def on_connect(client, userdata, flags, rc):
    print("[Gas Sensor] ✅ Connected.")
    client.subscribe(HEARTBEAT_TOPIC)

def on_disconnect(client, userdata, rc):
    print("[Gas Sensor] 🔌 Disconnected.")

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
client.on_disconnect = on_disconnect
client.on_message = on_message
client.reconnect_delay_set(1, 30)

# === CONNECT LOOP ===
while True:
    try:
        client.connect(BROKER, port=PORT)
        break
    except Exception as e:
        print(f"[Gas Sensor] 🔁 Retry: {e}")
        time.sleep(3)

client.loop_start()
print("[Gas Sensor] 🔄 Waiting for heartbeat and sending gas readings...")

# === MAIN LOOP ===
while True:
    if time.time() - last_heartbeat <= 10:
        gas_level = round(random.uniform(150, 1100), 2)
        pkt = {
            "device_id": DEVICE_ID,
            "sensor": "gas",
            "value": gas_level,
            "timestamp": get_timestamp()
        }
        if ENABLE_HMAC:
            pkt["hmac"] = sign(pkt)
        client.publish(TOPIC, json.dumps(pkt))
        print(f"[Gas Sensor] 📤 Gas Level: {gas_level} ppm")
    else:
        print("[Gas Sensor] ⏸ Paused (hub offline)")
    time.sleep(6)

