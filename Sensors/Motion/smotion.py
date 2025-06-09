import os
import random 
import time
import json
import ssl
import paho.mqtt.client as mqtt
from faker import Faker
from datetime import datetime

faker = Faker()
BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS = os.getenv("ENABLE_TLS", "false").lower() == "true"
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
PORT = 8883 if ENABLE_TLS else 1883

TOPIC = "building/zone1/motion/entrance"
HEARTBEAT_TOPIC = "hub/heartbeat"
last_heartbeat = time.time()

def get_formatted_timestamp():
    return datetime.now().strftime("%d/%b/%y %H:%M:%S")

def generate_motion():
    return "motion_detected" if faker.boolean(chance_of_getting_true=30) else "no_motion"

def on_connect(client, userdata, flags, rc):
    print("[Motion Sensor] ✅ Connected.")
    client.subscribe(HEARTBEAT_TOPIC)

def on_disconnect(client, userdata, rc):
    print("[Motion Sensor] 🔌 Disconnected.")

def on_message(client, userdata, msg):
    global last_heartbeat
    if msg.topic == HEARTBEAT_TOPIC:
        last_heartbeat = time.time()

client = mqtt.Client()
if ENABLE_AUTH:
    client.username_pw_set(USERNAME, PASSWORD)
if ENABLE_TLS:
    client.tls_set(ca_certs="/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.reconnect_delay_set(1, 30)

while True:
    try:
        client.connect(BROKER, port=PORT)
        break
    except Exception as e:
        print(f"[Motion Sensor] 🔁 Retrying connection: {e}")
        time.sleep(3)

client.loop_start()
print("[Motion Sensor] 🚶 Sending motion updates...")

while True:
    if time.time() - last_heartbeat <= 10:
        motion = generate_motion()
        payload = {
            "sensor": "motion",
            "value": motion,
            "timestamp": get_formatted_timestamp()
        }
        client.publish(TOPIC, json.dumps(payload))
        print(f"[Motion Sensor] 📤 {motion}")
    else:
        print("[Motion Sensor] ⏸ Paused (hub offline)")
    time.sleep(3)

