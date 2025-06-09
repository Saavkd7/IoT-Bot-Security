import os
import time
import json
import random
import ssl
import hmac
import hashlib
import paho.mqtt.client as mqtt
from faker import Faker
from datetime import datetime

faker = Faker()
BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS = os.getenv("ENABLE_TLS", "false").lower() == "true"
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
ENABLE_HMAC = os.getenv("ENABLE_HMAC", "true").lower() == "true"
PORT = 8883 if ENABLE_TLS else 1883
TOPIC = "building/zone1/motion/entrance"
HEARTBEAT_TOPIC = "hub/heartbeat"
HMAC_SECRET = os.getenv("HMAC_SECRET", "defaultsecret").encode()
DEVICE_ID = "sensor_motion_01"
last_heartbeat = time.time()

# HMAC signing
def sign(pkt):
    if not ENABLE_HMAC:
        return ""
    data = json.dumps({k: pkt[k] for k in sorted(pkt)}, separators=(',', ':'), sort_keys=True).encode()
    return hmac.new(HMAC_SECRET, data, hashlib.sha256).hexdigest()

# MQTT setup
client = mqtt.Client()
if ENABLE_AUTH:
    client.username_pw_set(USERNAME, PASSWORD)
if ENABLE_TLS:
    client.tls_set(ca_certs="/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)

def on_connect(client, userdata, flags, rc):
    print("[Motion Sensor] Connected.")
    client.subscribe(HEARTBEAT_TOPIC)

def on_message(client, userdata, msg):
    global last_heartbeat
    if msg.topic == HEARTBEAT_TOPIC:
        last_heartbeat = time.time()

client.on_connect = on_connect
client.on_message = on_message
client.reconnect_delay_set(1, 30)
client.connect(BROKER, port=PORT)
client.loop_start()
print("[Motion Sensor] Sending motion updates...")

state = "no_motion"
while True:
    if time.time() - last_heartbeat <= 10:
        if random.random() < 0.3:
            state = "motion_detected" if state == "no_motion" else "no_motion"
        pkt = {
            "device_id": DEVICE_ID,
            "sensor": "motion",
            "value": state,
            "timestamp": datetime.now().strftime("%d/%b/%y %H:%M:%S")
        }
        if ENABLE_HMAC:
            pkt["hmac"] = sign(pkt)
        client.publish(TOPIC, json.dumps(pkt))
        print(f"[Motion Sensor]  {state}")
    else:
        print("[Motion Sensor]  Paused (hub offline)")
    time.sleep(3)
