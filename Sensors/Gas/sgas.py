import os
import time
import json
import paho.mqtt.client as mqtt
from faker import Faker
from datetime import datetime

BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "iotuser")
PASSWORD = os.getenv("MQTT_PASSWORD", "iotpassword")



faker = Faker()
TOPIC = "building/zone3/gas/detection"

def get_formatted_timestamp():
    return datetime.now().strftime("%d/%b/%y %H:%M:%S")

def generate_gas_level():
    normal_gas_level = faker.pyfloat(left_digits=2, right_digits=2, min_value=30, max_value=70)
    if faker.boolean(chance_of_getting_true=10):
        return faker.pyfloat(left_digits=3, right_digits=2, min_value=300, max_value=500)
    return normal_gas_level

def main():

    client = mqtt.Client()
    client.username_pw_set(USERNAME, PASSWORD)
    client.connect(BROKER)
    print("[Gas Sensor] 🛑 I am ONLINE!")

    while True:
        gas_value = generate_gas_level()
        data = {"sensor": "gas", "value": gas_value, "timestamp": get_formatted_timestamp()}
        client.publish(TOPIC, json.dumps(data))
        print(f"[Gas Sensor] Published: {data}")
        time.sleep(5)

if __name__ == "__main__":
    main()

