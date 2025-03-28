import os
import time
import json
import paho.mqtt.client as mqtt
from faker import Faker
from datetime import datetime

faker = Faker()
BROKER_ADDRESS = os.getenv("BROKER_ADDRESS", "mqtt-broker")
TOPIC = "building/zone1/motion/entrance"

def get_formatted_timestamp():
    return datetime.now().strftime("%d/%m/%y %H:%M:%S")

def generate_motion():
    return "motion_detected" if faker.boolean(chance_of_getting_true=30) else "no_motion"

def main():
    client = mqtt.Client()
    client.connect(BROKER_ADDRESS)
    print("[Motion Sensor] 🚶 I am ONLINE!")

    while True:
        motion_value = generate_motion()
        data = {"sensor": "motion", "value": motion_value, "timestamp": get_formatted_timestamp()}
        client.publish(TOPIC, json.dumps(data))
        print(f"[Motion Sensor] Published: {data}")
        time.sleep(3)

if __name__ == "__main__":
    main()

