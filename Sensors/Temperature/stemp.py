import os
import json
import time
import math
import paho.mqtt.client as mqtt
from datetime import datetime

BROKER_ADDRESS = os.getenv("BROKER_ADDRESS", "mqtt_broker")
SENSOR_TOPIC = "building/zone2/temperature/room1"

def get_formatted_timestamp():
    # Returns timestamp as: day/AbbrMonth/yy HH:MM:SS (e.g., "31/Mar/23 15:45:02")
    return datetime.now().strftime("%d/%b/%y %H:%M:%S")

def get_season():
    month = datetime.now().month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"

def simulate_temperature(current_time):
    base_temp = 22.0
    amplitude = 2.0
    diurnal_variation = amplitude * math.sin(2 * math.pi * (current_time % 86400) / 86400)
    season = get_season()
    seasonal_offset = -1.0 if season == "winter" else (1.0 if season == "summer" else 0)
    return round(base_temp + diurnal_variation + seasonal_offset, 2)

def main():
    client = mqtt.Client()
    client.connect(BROKER_ADDRESS)
    print("[Temperature Sensor] 🌡️ I am ONLINE and publishing temperature data...")

    while True:
        now = time.time()
        temp = simulate_temperature(now)
        payload = {
            "sensor": "temperature",
            "value": temp,
            "timestamp": get_formatted_timestamp()
        }
        client.publish(SENSOR_TOPIC, json.dumps(payload))
        print(f"[Temperature Sensor] Published: {payload}")
        time.sleep(5)

if __name__ == "__main__":
    main()

