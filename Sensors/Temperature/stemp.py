import os
import json
import time
import math
import random
import paho.mqtt.client as mqtt
from datetime import datetime


BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "iotuser")
PASSWORD = os.getenv("MQTT_PASSWORD", "iotpassword")

SENSOR_TOPIC = "building/zone2/temperature/room1"

# Starting temperature
current_temp = 22.0

# Define average temps by season
seasonal_baseline = {
    "winter": 18.0,
    "spring": 21.0,
    "summer": 25.0,
    "autumn": 20.0
}

def get_formatted_timestamp():
    return datetime.now().strftime("%d/%m/%y %H:%M")

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

def get_day_factor():
    hour = datetime.now().hour
    # Simulate warmer temps during 10AM–4PM, cooler at night
    return math.cos((hour - 14) / 6) * -2  # Peak heat around 14:00

def simulate_temperature(current, season):
    baseline = seasonal_baseline[season]
    day_variation = get_day_factor()
    random_noise = random.uniform(-0.2, 0.2)
    drift = (baseline + day_variation - current) * 0.05
    return round(current + drift + random_noise, 2)

def main():
    global current_temp
    client = mqtt.Client()
    client.username_pw_set(USERNAME, PASSWORD)
    client.connect(BROKER)
    print("[Realistic Temp Sensor] 🌤️ ONLINE! Sending seasonal & daily variation data...")

    while True:
        season = get_season()
        current_temp = simulate_temperature(current_temp, season)
        payload = {
            "sensor": "temperature",
            "value": current_temp,
            "season": season,
            "timestamp": get_formatted_timestamp()
        }
        client.publish(SENSOR_TOPIC, json.dumps(payload))
        print(f"[Sensor] Published realistic temp: {payload}")
        time.sleep(5)

if __name__ == "__main__":
    main()

