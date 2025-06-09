import os
import json
import time
import random
import string
import paho.mqtt.client as mqtt

# MQTT CONFIG
BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
PORT = int(os.getenv("PORT", "1883"))
TOPIC = os.getenv("DDoS_TOPIC", "building/zone2/temperature/room1")

# Generate random device ID
def random_device_id():
    return "fake_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()

while True:
    payload = {
        "device_id": "sensor_temp_01",
        "sensor": random.choice(["temp", "gas", "motion"]),
        "value": round(random.uniform(0, 1200), 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    client.publish(TOPIC, json.dumps(payload))
    print(f"[FAKE] 🚨 {payload}")
    time.sleep(0.5)  # adjust speed as needed

