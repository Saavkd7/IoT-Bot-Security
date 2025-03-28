import os
import time
import json
import paho.mqtt.client as mqtt
from faker import Faker
from datetime import datetime

faker = Faker()
BROKER_ADDRESS = os.getenv("BROKER_ADDRESS", "mqtt-broker")
TOPIC = "building/zone3/gas/detection"

def get_formatted_timestamp():
    return datetime.now().strftime("%d/%m/%y")

def generate_gas_level():
    normal_gas_level = faker.pyfloat(left_digits=2, right_digits=2, min_value=30, max_value=70)
    # 10% chance for a dangerous gas leak
    if faker.boolean(chance_of_getting_true=10):
        return faker.pyfloat(left_digits=3, right_digits=2, min_value=300, max_value=500)
    return normal_gas_level

def main():
    client = mqtt.Client()
    client.connect(BROKER_ADDRESS)
    print("[Gas Sensor] 🛑 I am ONLINE!")

    while True:
        gas_value = generate_gas_level()
        data = {"sensor": "gas", "value": gas_value, "timestamp": get_formatted_timestamp()}
        client.publish(TOPIC, json.dumps(data))
        print(f"[Gas Sensor] Published: {data}")
        time.sleep(5)

if __name__ == "__main__":
    main()

